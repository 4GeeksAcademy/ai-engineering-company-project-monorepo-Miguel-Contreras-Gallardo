from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from services.reporting import api
from services.reporting.api import create_reporting_router


@pytest.fixture()
def reporting_client():
    app = FastAPI()
    db = Mock()

    def get_db():
        yield db

    app.include_router(create_reporting_router(get_db))
    with TestClient(app) as client:
        yield client, db


def report_row(**overrides):
    row = {
        "week_start": date(2026, 10, 26),
        "week_end": date(2026, 11, 2),
        "metric_code": "M01",
        "metric_name": "On-time delivery rate",
        "definition_version": "1.0",
        "metric_value": None,
        "unit": "percent",
        "status": "blocked",
        "status_reason": "Shipment denominator is unavailable",
        "dimensions": {"country": "US"},
        "numerator": None,
        "denominator": None,
        "source_watermark": None,
        "calculated_at": datetime(2026, 11, 2, tzinfo=timezone.utc),
        "run_id": "run-123",
    }
    row.update(overrides)
    return row


def test_weekly_report_returns_status_and_null_blocked_value(reporting_client):
    client, db = reporting_client
    db.execute.return_value.mappings.return_value.all.return_value = [report_row()]

    response = client.get("/reporting/executive/weekly")

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-10-26"
    assert body["week_end"] == "2026-11-02"
    assert body["metrics"][0]["metric_value"] is None
    assert body["metrics"][0]["status"] == "blocked"
    assert body["metrics"][0]["status_reason"] == "Shipment denominator is unavailable"
    assert body["metrics"][0]["metric_code"] == "M01"
    assert body["metrics"][0]["definition_version"] == "1.0"
    assert body["metrics"][0]["dimensions"] == {"country": "US"}
    assert db.execute.call_args.args[1] == {"week_start": None}


def test_weekly_report_accepts_requested_week(reporting_client):
    client, db = reporting_client
    db.execute.return_value.mappings.return_value.all.return_value = [report_row()]

    response = client.get(
        "/reporting/executive/weekly?week_start=2026-10-26"
    )

    assert response.status_code == 200
    assert db.execute.call_args.args[1] == {"week_start": date(2026, 10, 26)}


def test_weekly_report_returns_404_when_no_rows(reporting_client):
    client, db = reporting_client
    db.execute.return_value.mappings.return_value.all.return_value = []

    response = client.get("/reporting/executive/weekly")

    assert response.status_code == 404


def test_weekly_report_returns_503_for_storage_failure(reporting_client):
    client, db = reporting_client
    db.execute.side_effect = OperationalError("select", {}, Exception("offline"))

    response = client.get("/reporting/executive/weekly")

    assert response.status_code == 503
    assert response.json()["detail"] == "Executive reporting storage is unavailable"


def test_weekly_report_rejects_mixed_week_boundaries(reporting_client):
    client, db = reporting_client
    first = report_row()
    second = report_row(metric_code="M02", week_end=date(2026, 11, 3))
    db.execute.return_value.mappings.return_value.all.return_value = [first, second]

    response = client.get("/reporting/executive/weekly")

    assert response.status_code == 503


def test_week_start_must_be_a_date(reporting_client):
    client, _ = reporting_client

    response = client.get("/reporting/executive/weekly?week_start=not-a-date")

    assert response.status_code == 422


def test_week_start_must_be_a_monday(reporting_client):
    client, db = reporting_client

    response = client.get("/reporting/executive/weekly?week_start=2026-10-27")

    assert response.status_code == 422
    assert response.json()["detail"] == "week_start must be a Monday (UTC ISO-week boundary)"
    db.execute.assert_not_called()


def test_status_endpoint_returns_latest_run_metadata(reporting_client, monkeypatch):
    client, _ = reporting_client
    monkeypatch.setattr(
        api,
        "get_executive_report_status",
        lambda week_start: {
            "status": "blocked",
            "run": {
                "pipeline_name": "executive_weekly_report_flow",
                "week_start": "2026-10-26",
                "records_processed": 12,
                "aggregates_written": 1,
            },
        },
    )

    response = client.get("/reporting/executive/status?week_start=2026-10-26")

    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
    assert response.json()["run"]["aggregates_written"] == 1


def test_status_endpoint_returns_503_if_audit_log_unavailable(reporting_client, monkeypatch):
    from services.reporting.pipeline_interface import PipelineInterfaceError

    client, _ = reporting_client
    monkeypatch.setattr(
        api,
        "get_executive_report_status",
        Mock(side_effect=PipelineInterfaceError("private details")),
    )

    response = client.get("/reporting/executive/status")

    assert response.status_code == 503
    assert response.json()["detail"] == "Executive reporting run metadata is unavailable"


def test_manual_refresh_fails_closed_without_operator_configuration(reporting_client, monkeypatch):
    client, _ = reporting_client
    monkeypatch.delenv("REPORTING_OPERATOR_TOKEN", raising=False)

    response = client.post(
        "/reporting/executive/weekly/refresh",
        json={"week_start": "2026-10-26"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Manual reporting is not configured"


def test_manual_refresh_requires_operator_authentication(reporting_client, monkeypatch):
    client, _ = reporting_client
    monkeypatch.setenv("REPORTING_OPERATOR_TOKEN", "configured-test-token")

    response = client.post(
        "/reporting/executive/weekly/refresh",
        json={"week_start": "2026-10-26"},
        headers={"X-Reporting-Operator-Key": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Reporting operator authentication required"


def test_manual_refresh_dispatches_named_flow(reporting_client, monkeypatch):
    client, _ = reporting_client
    monkeypatch.setenv("REPORTING_OPERATOR_TOKEN", "configured-test-token")
    dispatch = Mock(
        return_value={
            "status": "blocked",
            "run": {"run_id": "run-123", "status": "blocked"},
            "deduplicated": False,
        }
    )
    monkeypatch.setattr(api, "request_executive_weekly_report", dispatch)

    response = client.post(
        "/reporting/executive/weekly/refresh",
        json={"week_start": "2026-10-26"},
        headers={
            "X-Reporting-Operator-Key": "configured-test-token",
            "Idempotency-Key": "refresh-2026-w44",
        },
    )

    assert response.status_code == 200
    assert response.json()["run"]["run_id"] == "run-123"
    dispatch.assert_called_once_with(
        date(2026, 10, 26), idempotency_key="refresh-2026-w44"
    )


def test_manual_refresh_rejects_non_monday_before_dispatch(reporting_client, monkeypatch):
    client, _ = reporting_client
    monkeypatch.setenv("REPORTING_OPERATOR_TOKEN", "configured-test-token")
    dispatch = Mock()
    monkeypatch.setattr(api, "request_executive_weekly_report", dispatch)

    response = client.post(
        "/reporting/executive/weekly/refresh",
        json={"week_start": "2026-10-27"},
        headers={"X-Reporting-Operator-Key": "configured-test-token"},
    )

    assert response.status_code == 422
    dispatch.assert_not_called()
