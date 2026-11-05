from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers import telemetry_reports
from app.services.response_cache import clear


@pytest.fixture()
def report_client(monkeypatch):
    now = datetime.now(timezone.utc)
    rows = [
        {
            "timestamp": (now - timedelta(minutes=i + 1)).isoformat(),
            "event_type": "api_latency_recorded",
            "tags": ["category:rendimiento", "event_class:technical"],
            "properties": {
                "serviceName": "inventory-api",
                "endpoint": "/inventory/stock",
                "httpMethod": "GET",
                "latencyMs": 100 + i,
                "statusCode": 200,
            },
        }
        for i in range(3)
    ]
    auth_rows = [
        {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "event_type": "login_failed",
            "properties": {},
        },
        {
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "event_type": "login_failed",
            "properties": {},
        },
        {
            "timestamp": (now - timedelta(hours=3)).isoformat(),
            "event_type": "login_succeeded",
            "properties": {},
        },
    ]
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def __init__(self, result_rows):
            self.result_rows = result_rows

        def json(self):
            return self.result_rows

    def fake_get(url, *, headers, timeout):
        calls.append((url, headers, timeout))
        params = parse_qs(urlparse(url).query)
        result_rows = auth_rows if params.get("event_type") == ["in.(login_failed,login_succeeded)"] else rows
        return FakeResponse(result_rows)

    clear()
    monkeypatch.setattr(telemetry_reports.settings, "supabase_service_role_key", "test-secret")
    monkeypatch.setattr(telemetry_reports.httpx, "get", fake_get)
    with TestClient(create_app()) as client:
        yield client, calls
    clear()


def test_report_endpoint_fetches_and_aggregates_telemetry(report_client):
    client, calls = report_client
    response = client.get("/telemetry/report")

    assert response.status_code == 200
    report = response.json()
    assert set(report) == {"period", "metrics"}
    assert set(report["period"]) == {"from", "to"}
    assert report["metrics"]["events_per_day"]
    assert report["metrics"]["events_per_day"][0]["event_count"] == 3
    assert report["metrics"]["error_rate_by_type"] == []
    assert report["metrics"]["auth_failure_rate"][0]["failed_attempts"] == 2
    assert report["metrics"]["auth_failure_rate"][0]["total_attempts"] == 3
    assert report["metrics"]["auth_failure_rate"][0]["failure_rate"] == pytest.approx(2 / 3)
    start = datetime.fromisoformat(report["period"]["from"])
    end = datetime.fromisoformat(report["period"]["to"])
    assert end - start == timedelta(days=7)
    assert len(calls) == 2
    assert calls[0][1]["Authorization"] == "Bearer test-secret"
    assert parse_qs(urlparse(calls[1][0]).query)["event_type"] == [
        "in.(login_failed,login_succeeded)"
    ]


def test_report_endpoint_caches_same_period(report_client):
    client, calls = report_client
    start = datetime.now(timezone.utc) - timedelta(hours=3)
    end = datetime.now(timezone.utc)
    params = {"start_date": start.isoformat(), "end_date": end.isoformat()}

    assert client.get("/telemetry/report", params=params).status_code == 200
    assert client.get("/telemetry/report", params=params).status_code == 200

    assert len(calls) == 2


def test_report_cache_uses_sixty_second_ttl(report_client, monkeypatch):
    client, calls = report_client
    original_get_or_set = telemetry_reports.get_or_set
    ttl_values = []

    def recording_get_or_set(key, loader, ttl_seconds):
        ttl_values.append(ttl_seconds)
        return original_get_or_set(key, loader, ttl_seconds)

    monkeypatch.setattr(telemetry_reports, "get_or_set", recording_get_or_set)
    params = {
        "start_date": "2026-11-05T00:00:00Z",
        "end_date": "2026-11-05T23:59:59Z",
    }

    assert client.get("/telemetry/report", params=params).status_code == 200
    assert ttl_values == [60.0]
    assert len(calls) == 2


def test_report_endpoint_caches_default_period(report_client):
    client, calls = report_client

    assert client.get("/telemetry/report").status_code == 200
    assert client.get("/telemetry/report").status_code == 200

    assert len(calls) == 2


def test_report_endpoint_rejects_invalid_range(report_client):
    client, calls = report_client
    start = datetime.now(timezone.utc)
    end = start - timedelta(hours=1)

    response = client.get(
        "/telemetry/report",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
    )

    assert response.status_code == 422
    assert calls == []
