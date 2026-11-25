"""Pure analysis functions for technical and operational telemetry reports."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import ceil
from statistics import mean
from typing import Any

# Business reporting dimensions (shipments, CX, commercial and executive KPIs) are
# deliberately excluded. Warehouse operations remain in scope alongside system,
# performance, error, authentication and backoffice telemetry.
IN_SCOPE_CATEGORIES = {
    "almacen",
    "autenticacion",
    "errores",
    "navegacion",
    "rendimiento",
    "tecnologia",
}


def _percentile(values: list[float], percentile: float) -> float | None:
    """Return a nearest-rank percentile for a non-empty list of values."""
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 2)


def _event_category(event: dict[str, Any]) -> str:
    """Read a category from normalized ingestion tags."""
    for tag in event.get("tags") or []:
        if isinstance(tag, str) and tag.startswith("category:"):
            return tag.partition(":")[2]
    return "unknown"


def _timestamp(event: dict[str, Any]) -> datetime | None:
    value = event.get("timestamp")
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_telemetry_report(
    events: list[dict[str, Any]],
    *,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any]:
    """Aggregate in-scope telemetry without deriving business KPIs."""
    start = period_start.astimezone(timezone.utc)
    end = period_end.astimezone(timezone.utc)
    included: list[dict[str, Any]] = []
    for event in events:
        category = _event_category(event)
        timestamp = _timestamp(event)
        if category not in IN_SCOPE_CATEGORIES or timestamp is None:
            continue
        if start <= timestamp <= end:
            included.append(event)

    event_counts = Counter(event.get("event_type", "unknown") for event in included)
    category_counts = Counter(_event_category(event) for event in included)
    sources = Counter(
        str(event.get("properties", {}).get("sourceApp", "unknown"))
        for event in included
    )

    timeline_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for event in included:
        timestamp = _timestamp(event)
        assert timestamp is not None
        bucket = timestamp.strftime("%Y-%m-%dT%H:00:00Z")
        timeline_counts[bucket][_event_category(event)] += 1
    timeline = [
        {
            "hour": hour,
            "total": sum(counts.values()),
            "by_category": dict(sorted(counts.items())),
        }
        for hour, counts in sorted(timeline_counts.items())
    ]

    latency_values = [
        float(properties["latencyMs"])
        for event in included
        if event.get("event_type") == "api_latency_recorded"
        and isinstance((properties := event.get("properties", {})).get("latencyMs"), (int, float))
    ]
    latency_by_endpoint: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for event in included:
        if event.get("event_type") != "api_latency_recorded":
            continue
        properties = event.get("properties", {})
        value = properties.get("latencyMs")
        if isinstance(value, (int, float)):
            key = (
                str(properties.get("serviceName", "unknown")),
                str(properties.get("endpoint", "unknown")),
                str(properties.get("httpMethod", "unknown")),
            )
            latency_by_endpoint[key].append(float(value))

    latency = {
        "count": len(latency_values),
        "average_ms": round(mean(latency_values), 2) if latency_values else None,
        "p50_ms": _percentile(latency_values, 0.50),
        "p95_ms": _percentile(latency_values, 0.95),
        "by_endpoint": [
            {
                "service": key[0],
                "endpoint": key[1],
                "method": key[2],
                "count": len(values),
                "average_ms": round(mean(values), 2),
                "p95_ms": _percentile(values, 0.95),
            }
            for key, values in sorted(latency_by_endpoint.items())
        ],
    }

    web_vitals: dict[str, list[float]] = defaultdict(list)
    for event in included:
        if event.get("event_type") != "web_vital_recorded":
            continue
        properties = event.get("properties", {})
        name, value = properties.get("metricName"), properties.get("metricValue")
        if isinstance(name, str) and isinstance(value, (int, float)):
            web_vitals[name].append(float(value))

    errors = Counter(
        str(event.get("properties", {}).get("errorCategory", event.get("event_type", "unknown")))
        for event in included
        if _event_category(event) == "errores"
    )
    status_counts = Counter(
        str(event.get("properties", {}).get("statusCode"))
        for event in included
        if event.get("event_type") == "api_latency_recorded"
        and isinstance(event.get("properties", {}).get("statusCode"), int)
    )
    operational_counts = Counter(
        event.get("event_type", "unknown")
        for event in included
        if _event_category(event) == "almacen"
    )

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "scope": {
            "categories": sorted(IN_SCOPE_CATEGORIES),
            "excluded_business_categories": [
                "comercial", "cx", "direccion", "logistica_inversa", "ultima_milla"
            ],
        },
        "event_count": len(included),
        "by_category": dict(sorted(category_counts.items())),
        "by_event_type": dict(sorted(event_counts.items())),
        "by_source_app": dict(sorted(sources.items())),
        "timeline_hourly": timeline,
        "technical": {
            "api_latency": latency,
            "http_status_counts": dict(sorted(status_counts.items())),
            "errors_by_category": dict(sorted(errors.items())),
            "web_vitals": {
                name: {
                    "count": len(values),
                    "average": round(mean(values), 2),
                    "p75": _percentile(values, 0.75),
                    "p95": _percentile(values, 0.95),
                }
                for name, values in sorted(web_vitals.items())
            },
        },
        "operations": {"warehouse_events": dict(sorted(operational_counts.items()))},
    }
