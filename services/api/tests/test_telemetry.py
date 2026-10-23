import logging

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _event(event_type: str = "shipment_delivered") -> dict:
    return {
        "eventId": "a1b2c3d4-e5f6-4a7b-9c0d-1e2f3a4b5c6d",
        "timestamp": "2026-10-22T14:30:00.000Z",
        "sessionId": "23de1bfd-7863-5f1d-9d2c-d6f91f9233d5",
        "userId": "urn:service:telemetry-emitter",
        "event_type": event_type,
        "schemaVersion": "1.0",
        "requestId": "a2bdcd21-db67-550c-85ca-5f1759fbfa4e",
        "properties": {"shipmentId": "9a8b7c6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d"},
    }


def test_capture_events_returns_count_and_logs_event_types(caplog):
    client = TestClient(create_app())

    with caplog.at_level(logging.INFO, logger="app.routers.telemetry"):
        response = client.post(
            "/telemetry/events",
            json={"events": [_event(), _event("order_picking_completed")]},
        )

    assert response.status_code == 200
    assert response.json() == {"received": 2}
    assert "Received 2 telemetry events" in caplog.text
    assert "shipment_delivered" in caplog.text
    assert "order_picking_completed" in caplog.text


def test_capture_events_accepts_empty_batch():
    client = TestClient(create_app())

    response = client.post("/telemetry/events", json={"events": []})

    assert response.status_code == 200
    assert response.json() == {"received": 0}


def test_capture_events_requires_standard_envelope_fields():
    event = _event()
    del event["eventId"]
    client = TestClient(create_app())

    response = client.post("/telemetry/events", json={"events": [event]})

    assert response.status_code == 422


def test_telemetry_endpoint_setting_reads_environment(monkeypatch):
    monkeypatch.setenv("TELEMETRY_ENDPOINT", "https://telemetry.example/events")

    settings = Settings(_env_file=None)

    assert settings.telemetry_endpoint == "https://telemetry.example/events"