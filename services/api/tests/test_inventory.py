from itertools import count

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Article, Lot, Movement, Warehouse
from app.routers.articles import delete_article
from app.services.inventory import InsufficientStock, get_reorder_items, query_stock, register_movement


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sequence = count(1)

    def assign_sequence(_mapper, _connection, movement):
        if movement.sequence is None:
            movement.sequence = next(sequence)

    event.listen(Movement, "before_insert", assign_sequence)
    Base.metadata.create_all(engine)
    session = Session(engine)
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

    try:
        yield session
    finally:
        session.close()
        event.remove(Movement, "before_insert", assign_sequence)
        engine.dispose()


def movement(db: Session, type_: str, quantity: int, key: str, direction=None):
    result = register_movement(
        db,
        sku="SKU-1",
        warehouse_id="LAX",
        lot_code="LOT-1",
        type_=type_,
        quantity=quantity,
        adjustment_direction=direction,
        reason="Conteo operativo",
        request_key=key,
    )
    db.commit()
    return result


def test_stock_is_derived_from_entries_outputs_and_adjustments(db: Session):
    assert movement(db, "entrada", 12, "entry").resulting_stock == 12
    assert movement(db, "salida", 3, "exit").resulting_stock == 9
    assert movement(db, "ajuste", 2, "adjust-up", "aumentar").resulting_stock == 11
    assert movement(db, "ajuste", 4, "adjust-down", "reducir").resulting_stock == 7

    stock = query_stock(db, "SKU-1")
    assert stock.total == 7
    assert {(line.warehouse_id, line.stock) for line in stock.lines} == {
        ("LAX", 7),
        ("ZAZ", 0),
    }


def test_reducing_adjustment_cannot_make_stock_negative(db: Session):
    movement(db, "entrada", 2, "entry")

    with pytest.raises(InsufficientStock):
        movement(db, "ajuste", 3, "adjust-down", "reducir")

    assert db.query(Movement).count() == 1
    assert query_stock(db, "SKU-1", "LAX").total == 2


def test_article_deactivation_preserves_ledger_and_hides_reorder_signal(db: Session):
    movement(db, "entrada", 2, "entry")

    delete_article("SKU-1", db)

    article = db.get(Article, "SKU-1")
    assert article is not None
    assert article.active is False
    assert db.query(Movement).count() == 1
    assert get_reorder_items(db).total_below_reorder == 0


def test_reorder_signal_uses_derived_stock(db: Session):
    assert get_reorder_items(db).items[0].current_stock == 0
    movement(db, "entrada", 6, "entry")
    assert get_reorder_items(db).total_below_reorder == 0