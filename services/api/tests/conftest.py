from itertools import count
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Article, Lot, Movement, Warehouse
from app.main import create_app
from app.routers import articles, inventory


@pytest.fixture()
def inventory_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sequence = count(1)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    def assign_sequence(_mapper, _connection, movement):
        if movement.sequence is None:
            movement.sequence = next(sequence)

    event.listen(Movement, "before_insert", assign_sequence)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with session_factory() as session:
        session.add_all(
            [
                Warehouse(id="LAX", name="Los Angeles"),
                Warehouse(id="ZAZ", name="Zaragoza"),
                Article(sku="SKU-1", name="Sensor", reorder_point=5),
            ]
        )
        session.flush()
        session.add(Lot(sku="SKU-1", code="LOT-1"))
        session.commit()

    def override_db():
        with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[articles.get_db] = override_db
    app.dependency_overrides[inventory.get_db] = override_db

    with TestClient(app) as client:
        yield SimpleNamespace(client=client, session_factory=session_factory)

    event.remove(Movement, "before_insert", assign_sequence)
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def movement_payload():
    def build(**overrides):
        payload = {
            "sku": "SKU-1",
            "warehouse_id": "LAX",
            "lot_code": "LOT-1",
            "type": "entrada",
            "quantity": 10,
            "adjustment_direction": None,
            "reason": "Recepción verificada",
            "request_key": "request-1",
        }
        payload.update(overrides)
        return payload

    return build