import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.reporting import pipeline_interface as interface


def test_status_reads_latest_terminal_record_from_pipeline_jsonl(tmp_path, monkeypatch):
    log_path = tmp_path / "pipeline-runs.jsonl"
    records = [
        {
            "run_id": "run-1",
            "pipeline_name": "executive_weekly_report_flow",
            "week_start": "2026-10-26",
            "started_at": "2026-11-02T07:00:00+00:00",
            "status": "running",
        },
        {
            "run_id": "run-1",
            "pipeline_name": "executive_weekly_report_flow",
            "week_start": "2026-10-26",
            "started_at": "2026-11-02T07:00:00+00:00",
            "finished_at": "2026-11-02T07:01:00+00:00",
            "aggregates_written": 1,
            "status": "blocked",
        },
        {
            "run_id": "run-2",
            "pipeline_name": "executive_weekly_report_flow",
            "week_start": "2026-11-02",
            "started_at": "2026-11-03T07:00:00+00:00",
            "status": "succeeded",
        },
    ]
    log_path.write_text("".join(json.dumps(record) + "\n" for record in records))
    monkeypatch.setattr(
        interface,
        "_pipeline_module",
        lambda: SimpleNamespace(RUN_LOG_PATH=log_path),
    )

    result = interface.get_executive_report_status(date(2026, 10, 26))

    assert result["status"] == "blocked"
    assert result["run"]["run_id"] == "run-1"
    assert result["run"]["aggregates_written"] == 1


def test_manual_dispatch_is_idempotent_for_week_and_key(tmp_path, monkeypatch):
    log_path = tmp_path / "pipeline-runs.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "run_id": "run-existing",
                "week_start": "2026-10-26",
                "idempotency_key": "refresh-key",
                "started_at": "2026-11-02T07:00:00+00:00",
                "status": "running",
            }
        )
        + "\n"
    )
    flow = Mock()
    pipeline = SimpleNamespace(
        RUN_LOG_DIR=tmp_path,
        RUN_LOG_PATH=log_path,
        executive_weekly_report_flow=flow,
    )
    monkeypatch.setattr(interface, "_pipeline_module", lambda: pipeline)

    result = interface.request_executive_weekly_report(
        date(2026, 10, 26), idempotency_key="refresh-key"
    )

    assert result["deduplicated"] is True
    assert result["run"]["run_id"] == "run-existing"
    flow.assert_not_called()


def test_manual_dispatch_calls_existing_prefect_flow(tmp_path, monkeypatch):
    log_path = tmp_path / "pipeline-runs.jsonl"
    flow = Mock(
        return_value={"status": "blocked", "run_id": "new-run", "metric_rows_written": 1}
    )
    pipeline = SimpleNamespace(
        RUN_LOG_DIR=tmp_path,
        RUN_LOG_PATH=log_path,
        executive_weekly_report_flow=flow,
    )
    monkeypatch.setattr(interface, "_pipeline_module", lambda: pipeline)

    result = interface.request_executive_weekly_report(
        date(2026, 10, 26), idempotency_key="new-key"
    )

    assert result == {
        "status": "blocked",
        "run": {"status": "blocked", "run_id": "new-run", "metric_rows_written": 1},
        "deduplicated": False,
    }
    flow.assert_called_once_with(
        date(2026, 10, 26), trigger_type="manual", idempotency_key="new-key"
    )


def test_manual_dispatch_rejects_non_monday():
    with pytest.raises(ValueError, match="Monday"):
        interface.request_executive_weekly_report(date(2026, 10, 27))
