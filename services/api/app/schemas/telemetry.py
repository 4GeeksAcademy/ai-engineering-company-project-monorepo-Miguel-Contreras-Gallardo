"""Pydantic schemas for the telemetry event envelope."""

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
    """A batch of telemetry events submitted to the temporary capture endpoint."""

    events: list[TelemetryEvent]


class TelemetryEventBatchResponse(BaseModel):
    received: int