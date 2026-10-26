"""Temporary telemetry capture endpoint for payload verification."""

import logging

from fastapi import APIRouter

from app.schemas.telemetry import TelemetryEventBatch, TelemetryEventBatchResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryEventBatchResponse)
def capture_events(batch: TelemetryEventBatch) -> TelemetryEventBatchResponse:
    """Log the received event types without persisting or forwarding the batch."""
    event_types = [event.event_type for event in batch.events]
    logger.info(
        "Received %d telemetry events; event_types=%s",
        len(batch.events),
        event_types,
    )
    return TelemetryEventBatchResponse(received=len(batch.events))