"""Telemetry event schemas (Pydantic models)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """Standard event envelope; detailed event validation is deferred to phase 3."""

    eventId: UUID
    timestamp: datetime
    sessionId: UUID
    userId: str
    event_type: str
    schemaVersion: str = Field(pattern=r"^\d+\.\d+$")
    requestId: UUID
    properties: dict[str, Any]


class TelemetryEventBatch(BaseModel):
    """Batch of telemetry events as expected by the /events endpoint."""

    events: list[TelemetryEvent]


class TelemetryEventBatchResponse(BaseModel):
    received: int
    stored: int
    rejected: int
