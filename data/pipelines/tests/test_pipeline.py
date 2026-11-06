from __future__ import annotations

from datetime import date, datetime, timezone
import logging
import json
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
    loaded = {"status": "blocked"}
    load_state = type(
        "FakeState",
        (),
        {"is_failed": lambda self: False, "result": lambda self: loaded, "name": "Completed"},
    )()

    def load(transformed, *, return_state=False):
        assert return_state is True
        calls.append("load")
        return load_state

    monkeypatch.setattr(pipeline, "load_weekly_kpis_task", load)
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
    assert result["load_state"] == "Completed"


def test_load_task_failure_is_returned_without_optional_export(monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline, "extract_sources_task", lambda week: {"staging_path": "unused"})
    monkeypatch.setattr(
        pipeline,
        "transform_validate_m01_task",
        lambda extraction, run_id: calls.append("transform") or {"rows": []},
    )
    failed_state = type("FakeState", (), {"is_failed": lambda self: True, "name": "Failed"})()

    def fail_load(transformed, *, return_state=False):
        assert return_state is True
        calls.append("load")
        return failed_state

    def unexpected_eval(*args, **kwargs):
        pytest.fail("optional export must not run after failed load")

    monkeypatch.setattr(pipeline, "load_weekly_kpis_task", fail_load)
    monkeypatch.setattr(pipeline, "create_eval_snapshot_task", unexpected_eval)
    monkeypatch.setattr(pipeline, "get_run_logger", lambda: logging.getLogger("test"))

    result = pipeline.executive_weekly_report_flow.fn(WEEK_START)

    assert result["status"] == "load_failed"
    assert result["load_state"] == "Failed"
    assert calls == ["transform", "load"]


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
    loaded = {"status": "blocked"}
    load_state = type(
        "FakeState",
        (),
        {"is_failed": lambda self: False, "result": lambda self: loaded, "name": "Completed"},
    )()

    def load(transformed, *, return_state=False):
        assert return_state is True
        return load_state

    monkeypatch.setattr(pipeline, "load_weekly_kpis_task", load)
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


def test_transform_cache_key_tracks_staging_content_and_task_metadata(tmp_path, monkeypatch):
    staging_dir = tmp_path / "raw"
    staging_dir.mkdir()
    monkeypatch.setattr(pipeline, "RAW_DIR", staging_dir)
    staged = staging_dir / "staging.json"
    staged.write_text('{"cohort_complete": false}', encoding="utf-8")
    parameters = {
        "extraction": {"week_start": WEEK_START.isoformat(), "staging_path": str(staged)},
        "run_id": "run-1",
    }
    first_key = pipeline._m01_transform_cache_key(None, parameters)
    assert pipeline.transform_validate_m01_task.cache_key_fn is pipeline._m01_transform_cache_key
    assert pipeline.transform_validate_m01_task.cache_expiration.total_seconds() == 6 * 60 * 60

    staged.write_text('{"cohort_complete": true}', encoding="utf-8")
    assert pipeline._m01_transform_cache_key(None, parameters) != first_key
    changed_run = {**parameters, "run_id": "run-2"}
    assert pipeline._m01_transform_cache_key(None, changed_run) != pipeline._m01_transform_cache_key(None, parameters)


def test_external_tasks_have_documented_retry_configuration():
    assert pipeline.extract_sources_task.retries == 2
    assert pipeline.extract_sources_task.retry_delay_seconds == [1, 3]
    assert pipeline.load_weekly_kpis_task.retries == 1
    assert pipeline.load_weekly_kpis_task.retry_delay_seconds == 2


def test_run_log_records_running_and_terminal_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "RUN_LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(pipeline, "RUN_LOG_PATH", tmp_path / "logs" / "runs.jsonl")
    pipeline._append_run_log({"run_id": "test-run", "status": "running"})
    pipeline._append_run_log({
        "run_id": "test-run",
        "started_at": "2026-10-26T07:00:00+00:00",
        "finished_at": "2026-10-26T07:00:02+00:00",
        "records_processed": 4,
        "status": "succeeded",
        "error_code": None,
    })

    entries = [json.loads(line) for line in pipeline.RUN_LOG_PATH.read_text().splitlines()]
    assert [entry["status"] for entry in entries] == ["running", "succeeded"]
    assert entries[1]["started_at"] and entries[1]["finished_at"]
    assert entries[1]["records_processed"] == 4
    assert entries[1]["error_code"] is None
    assert pipeline.RUN_LOG_DIR.stat().st_mode & 0o777 == 0o700
    assert pipeline.RUN_LOG_PATH.stat().st_mode & 0o777 == 0o600


def test_load_uses_briefing_unique_key_and_transactional_snapshot(monkeypatch):
    executed = []
    class FakeConnection:
        def execute(self, statement, parameters=None):
            executed.append((str(statement), parameters))
            return type("Result", (), {"scalar_one": lambda self: "reporting.executive_weekly_kpis"})()

    class Transaction:
        def __enter__(self):
            return FakeConnection()
        def __exit__(self, exc_type, exc, tb):
            return False

    class Engine:
        def begin(self):
            return Transaction()
        def dispose(self):
            pass

    monkeypatch.setattr(pipeline, "_get_destination_engine", lambda: Engine())
    row = {
        "week_start": WEEK_START.isoformat(), "week_end": "2026-10-26",
        "metric_code": "M01", "metric_name": "On-time delivery rate",
        "definition_version": "1.0", "metric_value": None, "unit": "percent",
        "status": "blocked", "status_reason": "missing cohort", "dimensions": {},
        "numerator": None, "denominator": None, "source_watermark": None,
        "calculated_at": "2026-10-26T07:00:00+00:00", "run_id": str(uuid4()),
    }
    result = pipeline.load_weekly_kpis_task.fn({
        "week_start": WEEK_START.isoformat(), "week_end": "2026-10-26",
        "status": "blocked", "rows": [row], "run_id": row["run_id"],
    })

    assert result["metric_rows_written"] == 1
    sql = "\n".join(statement for statement, _ in executed)
    assert "ON CONFLICT (week_start, week_end, metric_code, dimensions, definition_version)" in sql
    assert "pg_advisory_xact_lock" in sql
    assert "DELETE FROM reporting.executive_weekly_kpis" in sql
