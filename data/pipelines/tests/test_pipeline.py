from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from uuid import uuid4

import pytest

from data.pipelines import pipeline
from data.process.reporting.m01 import calculate_m01


WEEK_START = date(2026, 10, 19)


def shipment(*, country="US", delivered_at="2026-10-20T10:00:00Z", **overrides):
    row = {
        "shipment_id": str(uuid4()),
        "cohort_created_at": "2026-10-20T08:00:00Z",
        "country": country,
        "eligible": True,
        "promised_date": "2026-10-21T00:00:00Z",
        "delivered_at": delivered_at,
        "source_updated_at": "2026-10-22T00:00:00Z",
    }
    row.update(overrides)
    return row


def test_m01_blocks_without_authoritative_cohort():
    result = calculate_m01(
        week_start=WEEK_START,
        shipments=None,
        delivery_events=[],
        cohort_complete=False,
        source_watermark=None,
        run_id=str(uuid4()),
    )
    assert result.status == "blocked"
    assert result.metric_rows[0]["metric_value"] is None
    assert "authoritative shipment" in result.status_reason.lower()


def test_m01_calculates_global_and_country_from_complete_cohort():
    first = shipment()
    second = shipment(country="ES", delivered_at="2026-10-22T10:00:00Z")
    result = calculate_m01(
        week_start=WEEK_START,
        shipments=[first, second],
        delivery_events=[],
        cohort_complete=True,
        source_watermark=datetime(2026, 10, 23, tzinfo=timezone.utc),
        run_id=str(uuid4()),
    )
    assert result.status == "available"
    global_row = next(row for row in result.metric_rows if not row["dimensions"])
    assert global_row["metric_value"] == 50.0
    assert global_row["numerator"] == 1
    assert global_row["denominator"] == 2
    assert {row["dimensions"].get("country") for row in result.metric_rows[1:]} == {"US", "ES"}


def test_m01_does_not_publish_partial_country_dimensions():
    result = calculate_m01(
        week_start=WEEK_START,
        shipments=[shipment(country="US"), shipment(country=None)],
        delivery_events=[],
        cohort_complete=True,
        source_watermark=None,
        run_id=str(uuid4()),
    )
    assert len(result.metric_rows) == 1
    assert result.metric_rows[0]["dimensions"] == {}


def test_m01_blocks_if_an_eligible_shipment_lacks_promised_date():
    result = calculate_m01(
        week_start=WEEK_START,
        shipments=[shipment(promised_date=None)],
        delivery_events=[],
        cohort_complete=True,
        source_watermark=None,
        run_id=str(uuid4()),
    )
    assert result.status == "blocked"
    assert result.metric_rows[0]["metric_value"] is None
    assert "promised date" in result.status_reason.lower()


def test_m01_rejects_non_monday_week():
    with pytest.raises(ValueError, match="Monday"):
        calculate_m01(
            week_start=date(2026, 10, 20),
            shipments=[],
            delivery_events=[],
            cohort_complete=True,
            source_watermark=None,
            run_id=str(uuid4()),
        )


def test_extract_properties_deduplicates_and_enforces_telemetry_schema():
    event_id = str(uuid4())
    base = {
        "event_id": event_id,
        "event_type": "shipment_delivered",
        "schema_version": "1.0",
        "properties": {
            "shipmentId": str(uuid4()),
            "carrierName": "UPS",
            "deliveredAt": "2026-10-20T10:00:00Z",
            "onTime": True,
        },
    }
    assert len(pipeline._event_properties([base, base])) == 1
    invalid = {**base, "properties": {**base["properties"], "trackingNumber": "secret"}}
    with pytest.raises(pipeline.PipelineValidationError):
        pipeline._event_properties([invalid])


def test_flow_invokes_primary_tasks_and_optional_task_with_return_state(monkeypatch):
    calls = []
    monkeypatch.setattr(
        pipeline,
        "extract_sources_task",
        lambda week: calls.append("extract") or {"staging_path": "unused"},
    )
    monkeypatch.setattr(
        pipeline,
        "transform_validate_m01_task",
        lambda extraction, run_id: calls.append("transform") or {"rows": []},
    )
    monkeypatch.setattr(
        pipeline,
        "load_weekly_kpis_task",
        lambda transformed: calls.append("load") or {"status": "blocked"},
    )
    optional_state = type("FakeState", (), {"is_failed": lambda self: True, "name": "Failed"})()

    def optional(rows, *, return_state=False):
        assert return_state is True
        calls.append("optional")
        return optional_state

    monkeypatch.setattr(pipeline, "create_eval_snapshot_task", optional)
    monkeypatch.setattr(pipeline, "get_run_logger", lambda: logging.getLogger("test"))
    result = pipeline.executive_weekly_report_flow.fn(WEEK_START)
    assert calls == ["extract", "transform", "load", "optional"]
    assert result["status"] == "blocked"
    assert result["optional_eval_state"] == "Failed"


def test_optional_eval_task_failure_is_captured_by_prefect_flow(monkeypatch):
    """The flow's optional call must request a state instead of raising."""
    monkeypatch.setattr(
        pipeline,
        "extract_sources_task",
        lambda week: {"staging_path": "unused"},
    )
    monkeypatch.setattr(
        pipeline,
        "transform_validate_m01_task",
        lambda extraction, run_id: {
            "rows": [{
                "week_start": WEEK_START.isoformat(),
                "week_end": "2026-10-26",
                "metric_code": "M01",
                "metric_value": None,
                "unit": "percent",
                "status": "blocked",
                "dimensions": {},
            }]
        },
    )
    monkeypatch.setattr(
        pipeline,
        "load_weekly_kpis_task",
        lambda transformed: {"status": "blocked"},
    )
    monkeypatch.setattr(pipeline, "get_run_logger", lambda: logging.getLogger("test"))
    failed_state = type(
        "FakeState", (), {"is_failed": lambda self: True, "name": "Failed"}
    )()

    def fail_optional(rows, *, return_state=False):
        assert return_state is True
        return failed_state

    monkeypatch.setattr(pipeline, "create_eval_snapshot_task", fail_optional)
    result = pipeline.executive_weekly_report_flow.fn(WEEK_START)
    assert result["status"] == "blocked"
    assert result["optional_eval_state"] == "Failed"
