import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.engine import make_url

from app.config import settings
from app.db.models import Article, Lot, Movement
from app.services.inventory import (
    ConflictRequestKey,
    InsufficientStock,
    query_stock,
    register_movement,
)


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL is required for PostgreSQL acceptance tests",
)


@pytest.fixture(scope="module")
def postgres_env():
    database_url = make_url(TEST_DATABASE_URL)
    if database_url.get_backend_name() != "postgresql":
        pytest.skip("TEST_DATABASE_URL must use PostgreSQL")

    schema = f"inventory_acceptance_{uuid4().hex}"
    admin_engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(CreateSchema(schema))

    query = dict(database_url.query)
    query["options"] = f"-csearch_path={schema}"
    scoped_url = database_url.set(query=query)
    original_url = settings.database_url
    settings.database_url = scoped_url.render_as_string(hide_password=False)

    api_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(api_root / "alembic.ini"))
    command.upgrade(alembic_config, "head")

    engine = create_engine(scoped_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield session_factory
    finally:
        engine.dispose()
        settings.database_url = original_url
        with admin_engine.connect() as connection:
            connection.execute(DropSchema(schema, cascade=True))
        admin_engine.dispose()


@pytest.fixture(autouse=True)
def reset_postgres(postgres_env):
    with postgres_env.begin() as session:
        session.execute(text("TRUNCATE movements, lots, articles RESTART IDENTITY CASCADE"))
        session.add(Article(sku="SKU-1", name="Sensor", reorder_point=5))
        session.flush()
        session.add(Lot(sku="SKU-1", code="LOT-1"))


def register(session, *, type_="entrada", quantity=10, request_key="request-1"):
    return register_movement(
        session,
        sku="SKU-1",
        warehouse_id="LAX",
        lot_code="LOT-1",
        type_=type_,
        quantity=quantity,
        adjustment_direction=None,
        reason="Prueba concurrente",
        request_key=request_key,
    )


def test_inv_001_postgres_ledger_rejects_update_and_delete(postgres_env):
    with postgres_env.begin() as session:
        movement = register(session, quantity=4).movement

    with postgres_env() as session:
        with pytest.raises(DBAPIError):
            session.execute(
                update(Movement).where(Movement.id == movement.id).values(quantity=9)
            )
            session.commit()
        session.rollback()

        with pytest.raises(DBAPIError):
            session.execute(delete(Movement).where(Movement.id == movement.id))
            session.commit()
        session.rollback()

    with postgres_env() as session:
        persisted = session.get(Movement, movement.id)
        assert persisted.quantity == 4


def test_inv_002_postgres_identity_sequence_is_unique_and_increasing(postgres_env):
    with postgres_env.begin() as session:
        first = register(session, quantity=1, request_key="first").movement
        second = register(session, quantity=1, request_key="second").movement

    assert first.sequence < second.sequence
    with postgres_env() as session:
        assert session.scalar(select(func.count(func.distinct(Movement.sequence)))) == 2


@pytest.mark.parametrize(
    ("warehouse_id", "quantity"),
    [("UNKNOWN", 1), ("LAX", 0)],
)
def test_inv_005_and_inv_008_postgres_constraints_reject_invalid_movements(
    postgres_env, warehouse_id, quantity
):
    with postgres_env() as session:
        lot_id = session.scalar(select(Lot.id).where(Lot.sku == "SKU-1"))
        session.add(
            Movement(
                request_key=f"invalid-{warehouse_id}-{quantity}",
                sku="SKU-1",
                warehouse_id=warehouse_id,
                lot_id=lot_id,
                type="entrada",
                quantity=quantity,
                reason="Movimiento inválido",
            )
        )
        with pytest.raises(DBAPIError):
            session.commit()

    with postgres_env() as session:
        assert session.scalar(select(func.count()).select_from(Movement)) == 0


def test_inv_004_and_invariant_2_concurrent_outputs_never_make_stock_negative(
    postgres_env,
):
    with postgres_env.begin() as session:
        register(session, quantity=10, request_key="initial")

    barrier = Barrier(2)

    def output(request_key):
        try:
            with postgres_env.begin() as session:
                barrier.wait()
                register(
                    session,
                    type_="salida",
                    quantity=7,
                    request_key=request_key,
                )
            return "committed"
        except InsufficientStock:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(output, ["output-1", "output-2"]))

    assert sorted(results) == ["committed", "rejected"]
    with postgres_env() as session:
        assert query_stock(session, "SKU-1", "LAX", "LOT-1").total == 3
        assert session.scalar(select(func.count()).select_from(Movement)) == 2


def test_inv_009_concurrent_identical_replay_creates_one_movement(postgres_env):
    barrier = Barrier(2)

    def replay():
        with postgres_env.begin() as session:
            barrier.wait()
            return register(session, quantity=5, request_key="same-key")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: replay(), range(2)))

    assert results[0] == results[1]
    assert results[0].resulting_stock == 5
    with postgres_env() as session:
        assert session.scalar(select(func.count()).select_from(Movement)) == 1


def test_inv_009_concurrent_conflict_commits_one_and_rejects_one(postgres_env):
    barrier = Barrier(2)

    def submit(quantity):
        try:
            with postgres_env.begin() as session:
                barrier.wait()
                register(session, quantity=quantity, request_key="same-key")
            return "committed"
        except ConflictRequestKey:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, [4, 7]))

    assert sorted(results) == ["committed", "conflict"]
    with postgres_env() as session:
        assert session.scalar(select(func.count()).select_from(Movement)) == 1


def test_inv_010_and_invariant_4_reads_only_committed_movements(postgres_env):
    writer = postgres_env()
    reader = postgres_env()
    try:
        pending = register(writer, quantity=4, request_key="pending")
        assert pending.resulting_stock == 4
        assert query_stock(reader, "SKU-1", "LAX", "LOT-1").total == 0

        writer.commit()
        assert query_stock(reader, "SKU-1", "LAX", "LOT-1").total == 4
    finally:
        writer.close()
        reader.close()