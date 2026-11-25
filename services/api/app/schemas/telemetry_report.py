"""Response schema for technical and operational telemetry reports."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TelemetryReportResponse(BaseModel):
    """Aggregate report over technical and warehouse-operation events."""

    period: dict[str, datetime]
    scope: dict[str, Any]
    event_count: int
    by_category: dict[str, int]
    by_event_type: dict[str, int]
    by_source_app: dict[str, int]
    timeline_hourly: list[dict[str, Any]]
    technical: dict[str, Any]
    operations: dict[str, Any]
