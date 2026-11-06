from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from data.pipelines.pipeline import (
    PipelineValidationError,
    _event_properties,
    transform_validate_m01_task,
)


WEEK_START = date(2026, 10, 19)
RUN_ID = "a18f9a82-7a96-4c8f-a88c-97f1bb2abf18"


def shipment(*, delivered_at: str | None, promised_date: str = "2026-10-22T12:00:00Z", **overrides):
    row = {
        "shipment_id": str(uuid4()),
        "cohort_created_at": "2026-10-20T08:00:00Z",
        "country": "US",
        "eligible": True,
        "promised_date": promised_date,
        "delivered_at": delivered_at,
        "source_updated_at": "2026-10-25T00:00:00Z",
    }
    row.update(overrides)
    return row


def delivery_event(shipment_id: str, *, delivered_at: str, promised_date: str, on_time: bool):
    return {
        "shipmentId": shipment_id,
        "carrierName": "UPS",
        "deliveredAt": delivered_at,
        "promisedDate": promised_date,
        "onTime": on_time,
    }


def extract_properties(records):
    """Run only the pure event-envelope validation/deduplication task logic."""
    return _event_properties(records)


def test_m01_task_calculates_known_on_time_delivery_rate(tmp_path, monkeypatch):
    staging_dir = tmp_path / "raw"
    staging_dir.mkdir()
    monkeypatch.setattr("data.pipelines.pipeline.RAW_DIR", staging_dir)

    on_time = shipment(delivered_at="2026-10-21T11:00:00Z")
    late = shipment(delivered_at="2026-10-23T12:00:00Z")
    pending = shipment(delivered_at=None)
    extracted_events = [
        delivery_event(
            on_time["shipment_id"],
            delivered_at="2026-10-21T11:00:00Z",
            promised_date="2026-10-22T12:00:00Z",
            on_time=True,
        ),
        delivery_event(
            late["shipment_id"],
            delivered_at="2026-10-23T12:00:00Z",
            promised_date="2026-10-22T12:00:00Z",
            on_time=False,
        ),
    ]
    staging_file = staging_dir / "m01-test.json"
    import json

    staging_file.write_text(
        json.dumps(
            {
                "week_start": WEEK_START.isoformat(),
                "week_end": "2026-10-26",
                "delivery_properties": extracted_events,
                "shipments": [on_time, late, pending],
                "cohort_complete": True,
            }
        ),
        encoding="utf-8",
    )

    result = transform_validate_m01_task.fn(
        {
            "week_start": WEEK_START.isoformat(),
            "staging_path": str(staging_file),
            "source_watermark": "2026-10-25T00:00:00Z",
        },
        RUN_ID,
    )

    global_row = next(row for row in result["rows"] if row["dimensions"] == {})
    # One on-time shipment / all three eligible cohort shipments (including pending) = 33.3333%.
    assert result["status"] == "available"
    assert global_row["metric_code"] == "M01"
    assert global_row["numerator"] == 1
    assert global_row["denominator"] == 3
    assert global_row["metric_value"] == 33.3333


def test_m01_task_blocks_without_complete_authoritative_cohort(tmp_path, monkeypatch):
    staging_dir = tmp_path / "raw"
    staging_dir.mkdir()
    monkeypatch.setattr("data.pipelines.pipeline.RAW_DIR", staging_dir)
    staging_file = staging_dir / "m01-blocked.json"
    import json

    staging_file.write_text(
        json.dumps(
            {
                "week_start": WEEK_START.isoformat(),
                "delivery_properties": [],
                "shipments": None,
                "cohort_complete": False,
            }
        ),
        encoding="utf-8",
    )

    result = transform_validate_m01_task.fn(
        {"staging_path": str(staging_file), "source_watermark": None}, RUN_ID
    )

    assert result["status"] == "blocked"
    assert result["rows"][0]["metric_value"] is None
    assert result["rows"][0]["numerator"] is None
    assert result["rows"][0]["denominator"] is None


def test_m01_task_rejects_staging_path_outside_protected_raw_directory(tmp_path, monkeypatch):
    protected_raw = tmp_path / "raw"
    protected_raw.mkdir()
    outside = tmp_path / "untrusted.json"
    outside.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("data.pipelines.pipeline.RAW_DIR", protected_raw)

    with pytest.raises(PipelineValidationError, match="protected staging"):
        transform_validate_m01_task.fn(
            {"staging_path": str(outside)}, RUN_ID
        )


def test_m01_delivery_event_task_rejects_malformed_allowlist_payload():
    invalid_record = {
        "event_id": str(uuid4()),
        "event_type": "shipment_delivered",
        "schema_version": "1.0",
        "properties": {
            "shipmentId": str(uuid4()),
            "carrierName": "UPS",
            "deliveredAt": "2026-10-21T11:00:00Z",
            "onTime": True,
            "trackingNumber": "must-not-be-accepted",
        },
    }

    with pytest.raises(PipelineValidationError, match="allowlist"):
        extract_properties([invalid_record])
