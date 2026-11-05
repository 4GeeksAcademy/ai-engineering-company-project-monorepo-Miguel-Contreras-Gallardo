from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.routers import telemetry


def _event(event_type: str = "shipment_delivered") -> dict:
    properties = (
        {
            "shipmentId": str(uuid4()),
            "carrierName": "UPS",
            "deliveredAt": datetime.now(timezone.utc).isoformat(),
            "onTime": True,
        }
        if event_type == "shipment_delivered"
        else {
            "orderId": str(uuid4()),
            "warehouseLocation": "Zaragoza",
            "operatorId": "operator_opaque_01",
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "pickingTimeMinutes": 12,
        }
    )
    return {
        "eventId": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sessionId": str(uuid4()),
        "userId": "urn:service:telemetry-emitter",
        "event_type": event_type,
        "schemaVersion": "1.0",
        "requestId": str(uuid4()),
        "properties": properties,
    }


@pytest.fixture()
def telemetry_env(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    calls = []

    def fake_post(url, *, json, headers, timeout):
        calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return FakeResponse(json)

    monkeypatch.setattr(telemetry.settings, "supabase_service_role_key", "test-secret")
    monkeypatch.setattr(telemetry.httpx, "post", fake_post)
    app = create_app()
    with TestClient(app) as client:
        yield client, calls


def test_persists_valid_batch_and_reports_counts(telemetry_env):
    client, calls = telemetry_env
    events = [_event(), _event("order_picking_completed")]

    response = client.post("/telemetry/events", json={"events": events})

    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 2, "rejected": 0}
    assert calls[0]["url"] == telemetry.settings.supabase_telemetry_url
    assert len(calls[0]["json"]) == 2
    assert calls[0]["headers"]["Authorization"] == "Bearer test-secret"
    assert calls[0]["json"][0]["tags"] == [
        "category:ultima_milla",
        "event_type:shipment_delivered",
        "event_class:business",
        "carrier:UPS",
    ]
    assert calls[0]["json"][1]["tags"] == [
        "category:almacen",
        "event_type:order_picking_completed",
        "event_class:business",
        "warehouse:Zaragoza",
    ]
    assert len(calls) == 1


def test_mixed_batch_persists_valid_event_and_rejects_invalid_event(telemetry_env):
    client, calls = telemetry_env
    valid = _event()
    invalid = _event()
    invalid["timestamp"] = "not-a-timestamp"

    response = client.post("/telemetry/events", json={"events": [valid, invalid]})

    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 1, "rejected": 1}
    assert [event["event_id"] for event in calls[0]["json"]] == [valid["eventId"]]


@pytest.mark.parametrize(
    "event_type",
    ["incident_sla_breached", "frontend_error_recorded"],
)
def test_error_and_incident_events_are_tagged_technical(event_type, telemetry_env):
    properties = {
        "incidentId": str(uuid4()),
        "priority": "high",
        "assignedArea": "tecnologia",
        "slaDeadline": datetime.now(timezone.utc).isoformat(),
        "breachedAt": datetime.now(timezone.utc).isoformat(),
        "overdueHours": 1.5,
    }
    if event_type == "frontend_error_recorded":
        properties = {
            "errorCategory": "api_network_error",
            "sourceApp": "backoffice",
            "occurredAt": datetime.now(timezone.utc).isoformat(),
        }
    event = _event()
    event["event_type"] = event_type
    event["properties"] = properties
    client, calls = telemetry_env

    response = client.post("/telemetry/events", json={"events": [event]})

    assert response.status_code == 200
    assert response.json() == {"received": 1, "stored": 1, "rejected": 0}
    assert "event_class:technical" in calls[0]["json"][0]["tags"]


def test_event_without_event_id_is_rejected(telemetry_env):
    client, calls = telemetry_env
    event = _event()
    event.pop("eventId")

    response = client.post("/telemetry/events", json={"events": [event]})

    assert response.status_code == 200
    assert response.json() == {"received": 1, "stored": 0, "rejected": 1}
    assert calls == []


def test_empty_batch_returns_zero_counts(telemetry_env):
    client, calls = telemetry_env

    response = client.post("/telemetry/events", json={"events": []})

    assert response.status_code == 200
    assert response.json() == {"received": 0, "stored": 0, "rejected": 0}
    assert calls == []


@pytest.mark.parametrize("payload", [[], {}, {"events": None}, {"events": {}}])
def test_rejects_invalid_batch_envelope(payload, telemetry_env):
    client, _calls = telemetry_env

    response = client.post("/telemetry/events", json=payload)

    assert response.status_code == 422


def test_telemetry_endpoint_setting_reads_environment(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("TELEMETRY_ENDPOINT", "https://telemetry.example/events")
    settings = Settings(_env_file=None)
    assert settings.telemetry_endpoint == "https://telemetry.example/events"
