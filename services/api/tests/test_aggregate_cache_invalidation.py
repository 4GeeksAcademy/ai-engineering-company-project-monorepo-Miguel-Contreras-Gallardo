from app.models.audit_log import IncidentAuditLog
from app.models.incident import Incident
from app.services.response_cache import clear


def test_reorder_cache_invalidates_after_movement_and_article_write(inventory_env, movement_payload):
    clear()
    client = inventory_env.client

    assert client.get("/inventory/reorder").json()["total_below_reorder"] == 1
    response = client.post("/inventory/movements", json=movement_payload(quantity=10))
    assert response.status_code == 201
    assert client.get("/inventory/reorder").json()["total_below_reorder"] == 0

    response = client.post(
        "/articles/",
        json={"sku": "SKU-2", "name": "Gateway", "reorder_point": 2},
    )
    assert response.status_code == 201
    assert client.get("/inventory/reorder").json()["total_below_reorder"] == 1

    clear()


def test_incident_aggregate_caches_invalidate_after_writes(inventory_env):
    clear()
    engine = inventory_env.session_factory.kw["bind"]
    # Incident audit schema is registered with the second declarative base.
    from app.db.database import Base as IncidentBase

    IncidentBase.metadata.create_all(engine)
    try:
        with inventory_env.session_factory() as session:
            session.add(Incident(
                title="Cache test",
                description="Verify aggregates update after a write",
                channel="email",
                category="tecnologia",
                priority="alta",
                incident_type="incidencia",
                status="reported",
                created_by="test",
            ))
            session.commit()
        client = inventory_env.client
        # Prime cached empty aggregates, then exercise API creation for invalidation.
        assert client.get("/api/v1/incidents/stats").json()["total"] == 1
        assert client.get("/api/v1/incidents/open-by-severity").json()["total_open"] == 1
        response = client.post("/api/v1/incidents", json={
            "title": "Second cache test",
            "description": "A second incident to invalidate summaries",
            "channel": "email",
            "category": "tecnologia",
            "priority": "alta",
            "created_by": "test",
        })
        assert response.status_code == 201
        assert client.get("/api/v1/incidents/stats").json()["total"] == 2
        assert client.get("/api/v1/incidents/open-by-severity").json()["total_open"] == 2
    finally:
        clear()
