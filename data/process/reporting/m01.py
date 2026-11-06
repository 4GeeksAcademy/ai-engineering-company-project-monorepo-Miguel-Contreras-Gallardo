"""Pure M01 transformation for TrackFlow's weekly shipment cohort."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Shipment(BaseModel):
    """Approved source projection for one TrackFlow shipment."""

    model_config = ConfigDict(extra="forbid")

    shipment_id: UUID
    cohort_created_at: datetime
    country: str | None = None
    eligible: bool
    promised_date: datetime | None = None
    delivered_at: datetime | None = None
    source_updated_at: datetime | None = None


class DeliveryEvent(BaseModel):
    """Allowlisted shipment_delivered telemetry properties."""

    model_config = ConfigDict(extra="ignore")

    shipmentId: UUID
    carrierName: str
    deliveredAt: datetime
    promisedDate: datetime | None = None
    onTime: bool
    delayDays: int | None = Field(default=None, ge=0)


class M01Result(BaseModel):
    """M01 aggregate rows and explicit source-coverage status."""

    week_start: date
    week_end: date
    status: str
    status_reason: str | None
    metric_rows: list[dict[str, Any]]
    numerator: int | None
    denominator: int | None
    source_watermark: datetime | None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("M01 source timestamps must include a timezone")
    return value.astimezone(timezone.utc)


def _week_bounds(week_start: date) -> tuple[datetime, datetime, date]:
    if week_start.weekday() != 0:
        raise ValueError("week_start must be a Monday (UTC ISO-week boundary)")
    start = datetime.combine(week_start, time.min, tzinfo=timezone.utc)
    end_date = week_start + timedelta(days=7)
    return start, datetime.combine(end_date, time.min, tzinfo=timezone.utc), end_date


def _row(
    *,
    week_start: date,
    week_end: date,
    dimensions: dict[str, str],
    numerator: int | None,
    denominator: int | None,
    status: str,
    status_reason: str | None,
    source_watermark: datetime | None,
    calculated_at: datetime,
    run_id: str,
) -> dict[str, Any]:
    value = (
        round(numerator / denominator * 100, 4)
        if status == "available" and numerator is not None and denominator
        else None
    )
    return {
        "week_start": week_start,
        "week_end": week_end,
        "metric_code": "M01",
        "metric_name": "On-time delivery rate",
        "definition_version": "1.0",
        "metric_value": value,
        "unit": "percent",
        "status": status,
        "status_reason": status_reason,
        "dimensions": dimensions,
        "numerator": numerator,
        "denominator": denominator,
        "source_watermark": source_watermark,
        "calculated_at": calculated_at,
        "run_id": run_id,
    }


def calculate_m01(
    *,
    week_start: date,
    shipments: list[dict[str, Any]] | None,
    delivery_events: list[dict[str, Any]],
    cohort_complete: bool,
    source_watermark: datetime | None,
    run_id: str,
    calculated_at: datetime | None = None,
) -> M01Result:
    """Calculate M01, blocking unless the authoritative shipment cohort is complete.

    ``shipments`` must be the full authoritative TrackFlow shipment cohort with
    the documented projection. Telemetry contributes the delivery signal, not
    the denominator. A complete empty cohort and missing promised dates fail
    closed as blocked rather than yielding a misleading percentage.
    """
    start, end, week_end = _week_bounds(week_start)
    calculated_at = _utc(calculated_at or datetime.now(timezone.utc))
    if source_watermark is not None:
        source_watermark = _utc(source_watermark)
    if not run_id:
        raise ValueError("run_id is required")

    reason: str | None = None
    validated_shipments: list[Shipment] = []
    if shipments is None:
        reason = "Authoritative shipment cohort source is not configured"
    elif not cohort_complete:
        reason = "Shipment source has not certified a complete eligible cohort"
    else:
        try:
            validated_shipments = [Shipment.model_validate(row) for row in shipments]
        except (ValidationError, ValueError):
            reason = "Shipment source projection is invalid or incomplete"

    events: dict[UUID, list[DeliveryEvent]] = defaultdict(list)
    invalid_event_shipment_ids: set[UUID] = set()
    for item in delivery_events:
        try:
            event = DeliveryEvent.model_validate(item)
        except (ValidationError, ValueError):
            if isinstance(item, dict):
                try:
                    invalid_event_shipment_ids.add(UUID(str(item.get("shipmentId"))))
                except (TypeError, ValueError, AttributeError):
                    pass
            continue
        events[event.shipmentId].append(event)

    if reason is None:
        in_cohort = [
            shipment
            for shipment in validated_shipments
            if start <= _utc(shipment.cohort_created_at) < end and shipment.eligible
        ]
        if len({shipment.shipment_id for shipment in validated_shipments}) != len(validated_shipments):
            reason = "Shipment source contains duplicate shipment IDs"
        elif not in_cohort:
            reason = "No eligible shipments are available for the requested cohort"
        elif any(shipment.promised_date is None for shipment in in_cohort):
            reason = "Promised date is missing for one or more eligible shipments"
        else:
            for shipment in in_cohort:
                if shipment.shipment_id in invalid_event_shipment_ids:
                    reason = "Invalid delivery telemetry for an eligible shipment"
                    break
                shipment_events = events.get(shipment.shipment_id, [])
                if shipment_events and shipment.delivered_at is None:
                    reason = "Delivery telemetry conflicts with shipment source state"
                    break
                if shipment.delivered_at is not None:
                    source_delivered_at = _utc(shipment.delivered_at)
                    expected_on_time = source_delivered_at <= _utc(shipment.promised_date)  # type: ignore[arg-type]
                    for event in shipment_events:
                        if _utc(event.deliveredAt) != source_delivered_at:
                            reason = "Delivery timestamp conflicts between source and telemetry"
                            break
                        if event.promisedDate is not None and _utc(event.promisedDate) != _utc(shipment.promised_date):  # type: ignore[arg-type]
                            reason = "Promised date conflicts between source and telemetry"
                            break
                        if event.onTime != expected_on_time:
                            reason = "onTime conflicts with deliveredAt and promisedDate"
                            break
                    if reason is not None:
                        break
                    signatures = {
                        (_utc(event.deliveredAt), event.onTime, _utc(event.promisedDate) if event.promisedDate else None)
                        for event in shipment_events
                    }
                    if len(signatures) > 1:
                        reason = "Conflicting shipment_delivered events for shipmentId"
                        break

    if reason is not None:
        row = _row(
            week_start=week_start,
            week_end=week_end,
            dimensions={},
            numerator=None,
            denominator=None,
            status="blocked",
            status_reason=reason,
            source_watermark=source_watermark,
            calculated_at=calculated_at,
            run_id=run_id,
        )
        return M01Result(
            week_start=week_start,
            week_end=week_end,
            status="blocked",
            status_reason=reason,
            metric_rows=[row],
            numerator=None,
            denominator=None,
            source_watermark=source_watermark,
        )

    global_groups: dict[str | None, list[Shipment]] = defaultdict(list)
    for shipment in in_cohort:
        global_groups[None].append(shipment)
    if all(shipment.country for shipment in in_cohort):
        for shipment in in_cohort:
            global_groups[shipment.country].append(shipment)

    metric_rows: list[dict[str, Any]] = []
    global_numerator = 0
    global_denominator = len(in_cohort)
    for country, group in global_groups.items():
        on_time = sum(
            1
            for shipment in group
            if shipment.delivered_at is not None
            and _utc(shipment.delivered_at) <= _utc(shipment.promised_date)  # type: ignore[arg-type]
        )
        if country is None:
            global_numerator = on_time
            dimensions: dict[str, str] = {}
        else:
            dimensions = {"country": country}
        metric_rows.append(
            _row(
                week_start=week_start,
                week_end=week_end,
                dimensions=dimensions,
                numerator=on_time,
                denominator=len(group),
                status="available",
                status_reason=None,
                source_watermark=source_watermark,
                calculated_at=calculated_at,
                run_id=run_id,
            )
        )

    return M01Result(
        week_start=week_start,
        week_end=week_end,
        status="available",
        status_reason=None,
        metric_rows=metric_rows,
        numerator=global_numerator,
        denominator=global_denominator,
        source_watermark=source_watermark,
    )
