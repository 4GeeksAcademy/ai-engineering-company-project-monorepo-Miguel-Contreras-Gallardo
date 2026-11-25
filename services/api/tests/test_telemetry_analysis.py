from datetime import datetime, timezone

from app.services.telemetry_analysis import build_telemetry_report


def _event(event_type, category, timestamp, properties=None):
    return {
        "event_type": event_type,
        "timestamp": timestamp,
        "tags": [f"category:{category}"],
        "properties": properties or {},
    }


def test_report_aggregates_technical_and_operational_events_and_excludes_business():
    start = datetime(2026, 11, 5, tzinfo=timezone.utc)
    end = datetime(2026, 11, 6, tzinfo=timezone.utc)
    events = [
        _event("api_latency_recorded", "rendimiento", "2026-11-05T10:05:00Z", {
            "serviceName": "inventory-api", "endpoint": "/inventory/stock",
            "httpMethod": "GET", "latencyMs": 100, "statusCode": 200,
        }),
        _event("api_latency_recorded", "rendimiento", "2026-11-05T10:06:00Z", {
            "serviceName": "inventory-api", "endpoint": "/inventory/stock",
            "httpMethod": "GET", "latencyMs": 300, "statusCode": 500,
        }),
        _event("frontend_error_recorded", "errores", "2026-11-05T10:07:00Z", {
            "errorCategory": "api_http_error", "sourceApp": "backoffice",
        }),
        _event("web_vital_recorded", "rendimiento", "2026-11-05T11:01:00Z", {
            "metricName": "LCP", "metricValue": 2200,
        }),
        _event("order_picking_completed", "almacen", "2026-11-05T11:02:00Z", {
            "warehouseLocation": "Zaragoza",
        }),
        _event("shipment_delivered", "ultima_milla", "2026-11-05T11:02:00Z", {}),
        _event("api_latency_recorded", "rendimiento", "2026-11-07T11:02:00Z", {
            "latencyMs": 999,
        }),
    ]

    report = build_telemetry_report(events, period_start=start, period_end=end)

    assert report["event_count"] == 5
    assert report["by_category"] == {"almacen": 1, "errores": 1, "rendimiento": 3}
    assert "shipment_delivered" not in report["by_event_type"]
    assert report["technical"]["api_latency"]["count"] == 2
    assert report["technical"]["api_latency"]["average_ms"] == 200
    assert report["technical"]["api_latency"]["p95_ms"] == 300
    assert report["technical"]["http_status_counts"] == {"200": 1, "500": 1}
    assert report["technical"]["errors_by_category"] == {"api_http_error": 1}
    assert report["technical"]["web_vitals"]["LCP"]["average"] == 2200
    assert report["operations"]["warehouse_events"] == {"order_picking_completed": 1}
    assert len(report["timeline_hourly"]) == 2


def test_report_handles_empty_period():
    start = datetime(2026, 11, 5, tzinfo=timezone.utc)
    report = build_telemetry_report([], period_start=start, period_end=start)

    assert report["event_count"] == 0
    assert report["technical"]["api_latency"]["average_ms"] is None
    assert report["timeline_hourly"] == []
