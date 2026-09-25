"""Inventory domain service — all stock is derived from movements."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, case, func, select, text, update
from sqlalchemy.orm import Session, joinedload

from app.db.models import Article, Lot, Movement, Warehouse
from app.schemas.inventory import (
    MovementResult,
    MovementResponse,
    ReorderItem,
    ReorderResponse,
    StockLine,
    StockQueryResponse,
)


# ── Exceptions ──────────────────────────────────────────────────────


class InventoryError(Exception):
    """Base inventory error."""


class InsufficientStock(InventoryError):
    """Raised when a salida would make stock negative."""


class ConflictRequestKey(InventoryError):
    """Raised when request_key is reused with different data."""


class IdempotentReplay(Exception):
    """Internal signal: the request_key matched with identical data — replay."""


class ResourceNotFound(InventoryError):
    """SKU, warehouse or lot not found."""


# ── Helpers ──────────────────────────────────────────────────────────


def _stock_query(
    db: Session,
    sku: str,
    warehouse_id: Optional[str] = None,
    lot_id: Optional[int] = None,
) -> List[Tuple[int, int, str]]:
    """Return (lot_id, stock, lot_code) rows for the given filters."""
    stmt = (
        select(
            Lot.id.label("lot_id"),
            func.coalesce(
                func.sum(
                    case(
                        (Movement.type == "entrada", Movement.quantity),
                        (Movement.type.in_(["salida", "ajuste"]), -Movement.quantity),
                        else_=0,
                    )
                ),
                0,
            ).label("stock"),
            Lot.code.label("lot_code"),
        )
        .select_from(Lot)
        .outerjoin(
            Movement,
            and_(
                Movement.lot_id == Lot.id,
                Movement.sku == Lot.sku,
                Movement.warehouse_id == warehouse_id if warehouse_id else text("1=1"),
            ),
        )
        .where(Lot.sku == sku)
        .group_by(Lot.id, Lot.code)
    )

    if lot_id is not None:
        stmt = stmt.where(Lot.id == lot_id)

    # When warehouse_id is given, filter movements by warehouse
    # (but still show the lot even if no movements in that warehouse)
    if warehouse_id:
        stmt = stmt.where(
            and_(
                Lot.sku == sku,
                # Only sum movements from this warehouse
                Movement.warehouse_id == warehouse_id,
            )
        )

    result = db.execute(stmt).all()
    # If we filtered by lot and got nothing, the lot doesn't exist
    if lot_id is not None and not result:
        lot = db.get(Lot, lot_id)
        if lot is None or lot.sku != sku:
            raise ResourceNotFound(f"Lot {lot_id} not found or not associated with SKU {sku}")
        result = [(lot.id, 0, lot.code)]  # exists but no movements

    return result


def _validate_existence(db: Session, sku: str, warehouse_id: str, lot_code: str) -> Tuple[Article, Warehouse, Lot]:
    """Verify SKU, warehouse and lot (by code+sku) exist. Raise if not."""
    article = db.get(Article, sku)
    if article is None:
        raise ResourceNotFound(f"Article SKU '{sku}' not found")

    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise ResourceNotFound(f"Warehouse '{warehouse_id}' not found")

    lot = (
        db.query(Lot)
        .filter(Lot.sku == sku, Lot.code == lot_code)
        .first()
    )
    if lot is None:
        raise ResourceNotFound(f"Lot code '{lot_code}' not found for SKU '{sku}'")

    return article, warehouse, lot


# ── Core service ─────────────────────────────────────────────────────


def register_movement(
    db: Session,
    *,
    sku: str,
    warehouse_id: str,
    lot_code: str,
    type_: str,
    quantity: int,
    reason: Optional[str] = None,
    request_key: str,
) -> MovementResult:
    """Register a movement and return it together with the resulting stock.

    Idempotent by *request_key*: same key + same data ⇒ replay original result;
    same key + different data ⇒ ConflictRequestKey.
    Stock is always calculated from the movement ledger — never stored directly.
    """
    # 1 — Idempotency check
    existing = db.query(Movement).filter(Movement.request_key == request_key).first()
    if existing is not None:
        return _handle_idempotent_replay(db, existing, sku, warehouse_id, lot_code, type_, quantity)

    # 2 — Validate existence
    article, warehouse, lot = _validate_existence(db, sku, warehouse_id, lot_code)

    # 3 — Inside transaction: check stock for salida
    if type_ == "salida":
        current_stock = _stock_query(db, sku, warehouse_id, lot.id)[0][1]
        if current_stock < quantity:
            raise InsufficientStock(
                f"Insufficient stock for SKU '{sku}' lot '{lot_code}' "
                f"in warehouse '{warehouse_id}': "
                f"available={current_stock}, requested={quantity}"
            )

    # 4 — Insert movement
    now = datetime.now(timezone.utc)
    movement = Movement(
        sku=sku,
        warehouse_id=warehouse_id,
        lot_id=lot.id,
        type=type_,
        quantity=quantity,
        reason=reason,
        request_key=request_key,
        recorded_at=now,
    )
    db.add(movement)
    db.flush()  # get id

    # Assign the monotonic sequence from the auto-increment id
    movement.sequence = movement.id
    db.flush()

    # 5 — Compute resulting stock
    resulting_stock = _stock_query(db, sku, warehouse_id, lot.id)[0][1]

    return MovementResult(
        movement=_movement_to_response(movement),
        resulting_stock=resulting_stock,
    )


def _handle_idempotent_replay(
    db: Session,
    existing: Movement,
    sku: str,
    warehouse_id: str,
    lot_code: str,
    type_: str,
    quantity: int,
) -> MovementResult:
    """Check replay vs conflict for an existing request_key."""
    # Compare all relevant fields
    lot = db.query(Lot).filter(Lot.sku == sku, Lot.code == lot_code).first()
    lot_id_match = lot is not None and lot.id == existing.lot_id
    if (
        existing.sku == sku
        and existing.warehouse_id == warehouse_id
        and lot_id_match
        and existing.type == type_
        and existing.quantity == quantity
    ):
        # Replay — reconstruct the original stock result
        # Sum only movements of that lot+warehouse up to the original sequence
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (Movement.type == "entrada", Movement.quantity),
                        (Movement.type.in_(["salida", "ajuste"]), -Movement.quantity),
                        else_=0,
                    )
                ),
                0,
            )
        ).where(
            Movement.lot_id == existing.lot_id,
            Movement.sku == existing.sku,
            Movement.warehouse_id == existing.warehouse_id,
            Movement.sequence <= existing.sequence,
        )
        resulting_stock = db.scalar(stmt)
        return MovementResult(
            movement=_movement_to_response(existing),
            resulting_stock=resulting_stock,
        )
    else:
        raise ConflictRequestKey(
            f"Request key '{existing.request_key}' already used with different data"
        )


def _movement_to_response(m: Movement) -> MovementResponse:
    return MovementResponse(
        id=m.id,
        sequence=m.sequence,
        sku=m.sku,
        warehouse_id=m.warehouse_id,
        lot_id=m.lot_id,
        type=m.type,
        quantity=m.quantity,
        reason=m.reason,
        recorded_at=m.recorded_at,
    )


# ── Stock queries ────────────────────────────────────────────────────


def query_stock(
    db: Session,
    sku: str,
    warehouse_id: Optional[str] = None,
    lot_code: Optional[str] = None,
) -> StockQueryResponse:
    """Query stock for a SKU, optionally filtered by warehouse and/or lot code.

    Raises ResourceNotFound if the SKU does not exist.
    Raises ValueError if lot_code is given without warehouse_id.
    """
    article = db.get(Article, sku)
    if article is None:
        raise ResourceNotFound(f"Article SKU '{sku}' not found")

    if lot_code and not warehouse_id:
        raise ValueError("lot_code requires warehouse_id")

    lot_id: Optional[int] = None
    lot_filter: Optional[Lot] = None
    if lot_code:
        lot_filter = (
            db.query(Lot).filter(Lot.sku == sku, Lot.code == lot_code).first()
        )
        if lot_filter is None:
            raise ResourceNotFound(f"Lot code '{lot_code}' not found for SKU '{sku}'")
        lot_id = lot_filter.id

    rows = _stock_query(db, sku, warehouse_id, lot_id)

    lines = []
    for lot_id_val, stock, lot_code_val in rows:
        # For warehouse-filtered queries, only show that warehouse
        line_warehouse = warehouse_id
        lines.append(
            StockLine(
                warehouse_id=line_warehouse if line_warehouse else "all",
                lot_id=lot_id_val,
                lot_code=lot_code_val,
                stock=stock,
            )
        )

    total = sum(line.stock for line in lines)
    return StockQueryResponse(sku=sku, lines=lines, total=total)


def get_reorder_items(db: Session) -> ReorderResponse:
    """Return all articles whose current stock is at or below the reorder point."""
    articles = db.query(Article).all()
    items: List[ReorderItem] = []

    for article in articles:
        rows = _stock_query(db, article.sku, warehouse_id=None, lot_id=None)
        current_stock = sum(row[1] for row in rows)
        if current_stock <= article.reorder_point:
            items.append(
                ReorderItem(
                    sku=article.sku,
                    name=article.name,
                    reorder_point=article.reorder_point,
                    current_stock=current_stock,
                )
            )

    return ReorderResponse(items=items, total_below_reorder=len(items))