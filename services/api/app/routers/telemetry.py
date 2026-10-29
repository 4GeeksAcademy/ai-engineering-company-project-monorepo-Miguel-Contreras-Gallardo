"""Telemetry ingestion endpoint with per-event validation and bulk persistence."""

import json
import logging
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Body, HTTPException
from pydantic import ValidationError

from app.config import settings
from app.schemas.telemetry import TelemetryEvent, TelemetryEventBatchResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telemetry", tags=["telemetry"])

_registry_candidates = [
    Path(__file__).resolve().parents[4] / "docs/telemetry/event-schemas.json",
    Path(__file__).resolve().parents[2] / "data/telemetry/event-schemas.json",
]
_registry_path = next((path for path in _registry_candidates if path.is_file()), None)
if _registry_path is None:
    raise RuntimeError("Telemetry event schema registry is unavailable")
with _registry_path.open(encoding="utf-8") as registry_file:
    EVENT_SCHEMAS = json.load(registry_file)["event_schemas"]

TECHNICAL_EVENT_CATEGORIES = {
    "autenticacion",
    "errores",
    "navegacion",
    "rendimiento",
    "tecnologia",
}


def derive_tags(event_type: str, properties: dict[str, Any]) -> list[str]:
    """Derive non-sensitive event dimensions without modifying the envelope."""
    category = EVENT_SCHEMAS[event_type].get("category", "unknown")
    tags = [f"category:{category}", f"event_type:{event_type}"]
    event_class = (
        "technical"
        if category in TECHNICAL_EVENT_CATEGORIES
        else "business"
    )
    tags.append(f"event_class:{event_class}")

    dimensions = {
        "warehouseLocation": "warehouse",
        "carrierName": "carrier",
        "sourceApp": "source_app",
        "pageRoute": "page_route",
        "metricName": "metric_name",
        "metricRating": "metric_rating",
    }
    for property_name, tag_name in dimensions.items():
        value = properties.get(property_name)
        if isinstance(value, str) and value and len(value) <= 80:
            tags.append(f"{tag_name}:{value}")
    return tags

@router.post("/events", response_model=TelemetryEventBatchResponse)
def capture_events(
    payload: Any = Body(...),
) -> TelemetryEventBatchResponse:
    """Validate each raw event independently and bulk-insert valid records."""
    if not isinstance(payload, Mapping) or not isinstance(payload.get("events"), list):
        raise HTTPException(
            status_code=422,
            detail="Request body must be an object containing an events array",
        )

    raw_events = payload["events"]
    if not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=503,
            detail="Telemetry storage is not configured",
        )

    valid_records: list[dict[str, Any]] = []
    rejected = 0

    for index, raw_event in enumerate(raw_events):
        try:
            event = TelemetryEvent.model_validate(raw_event)
            schema = EVENT_SCHEMAS.get(event.event_type)
            if schema is None:
                raise ValueError("event_type is not present in the event registry")
            properties = event.properties
            unknown_properties = set(properties) - set(schema["allowlist"])
            missing_properties = set(schema.get("required", [])) - set(properties)
            if unknown_properties or missing_properties:
                raise ValueError(
                    "properties violate the event allowlist/required keys"
                )
            now = datetime.now(timezone.utc)
            timestamp = event.timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            if timestamp > now + timedelta(minutes=5):
                raise ValueError("timestamp is more than 5 minutes in the future")
            if timestamp < now - timedelta(hours=24):
                raise ValueError("timestamp is more than 24 hours old")
            valid_records.append(
                {
                    "event_id": str(event.eventId),
                    "timestamp": timestamp.isoformat(),
                    "session_id": str(event.sessionId),
                    "user_id": event.userId,
                    "event_type": event.event_type,
                    "schema_version": event.schemaVersion,
                    "request_id": str(event.requestId),
                    "properties": event.properties,
                    "tags": derive_tags(event.event_type, properties),
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        except (ValidationError, TypeError, ValueError) as error:
            rejected += 1
            logger.info("Rejected telemetry event at index %d: %s", index, error)

    stored = 0
    if valid_records:
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        try:
            response = httpx.post(
                settings.supabase_telemetry_url,
                json=valid_records,
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            inserted = response.json()
            if not isinstance(inserted, list):
                raise ValueError("Supabase REST response was not an array")
            stored = len(inserted)
            rejected += len(valid_records) - stored
        except (httpx.HTTPError, TypeError, ValueError):
            logger.exception("Failed to persist telemetry batch to Supabase")
            raise HTTPException(
                status_code=502,
                detail="Telemetry storage request failed",
            ) from None

    return TelemetryEventBatchResponse(
        received=len(raw_events),
        stored=stored,
        rejected=rejected,
    )
