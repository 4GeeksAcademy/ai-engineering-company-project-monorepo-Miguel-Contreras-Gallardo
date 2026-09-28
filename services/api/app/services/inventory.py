"""Inventory domain service — all stock is derived from movements."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import and_, case, func, select, true
from sqlalchemy.orm import Session

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
) -> List[Tuple[int, str, int, str]]:
    """Return (lot_id, warehouse_id, stock, lot_code) rows."""
    movement_delta = case(
        (Movement.type == "entrada", Movement.quantity),
        (Movement.type == "salida", -Movement.quantity),
        (
            and_(
                Movement.type == "ajuste",
                Movement.adjustment_direction == "aumentar",
            ),
            Movement.quantity,
        ),
        else_=-Movement.quantity,
    )
    stmt = (
        select(
            Lot.id.label("lot_id"),
            Warehouse.id.label("warehouse_id"),
            func.coalesce(func.sum(movement_delta), 0).label("stock"),
            Lot.code.label("lot_code"),
        )
        .select_from(Lot)
        .join(Warehouse, true())
        .outerjoin(
            Movement,
            and_(
                Movement.lot_id == Lot.id,
                Movement.sku == Lot.sku,
                Movement.warehouse_id == Warehouse.id,
            ),
        )
        .where(Lot.sku == sku)
        .group_by(Lot.id, Warehouse.id, Lot.code)
    )

    if warehouse_id is not None:
        stmt = stmt.where(Warehouse.id == warehouse_id)
    if lot_id is not None:
        stmt = stmt.where(Lot.id == lot_id)

    result = db.execute(stmt).all()
    if lot_id is not None and not result:
        lot = db.get(Lot, lot_id)
        if lot is None or lot.sku != sku:
            raise ResourceNotFound(f"Lot {lot_id} not found or not associated with SKU {sku}")

    return result


def _validate_existence(db: Session, sku: str, warehouse_id: str, lot_code: str) -> Tuple[Article, Warehouse, Lot]:
    """Verify SKU, warehouse and lot (by code+sku) exist. Raise if not."""
    article = db.get(Article, sku)
    if article is None or not article.active:
        raise ResourceNotFound(f"Article SKU '{sku}' not found")

    warehouse = db.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise ResourceNotFound(f"Warehouse '{warehouse_id}' not found")

    lot = (
        db.query(Lot)
        .filter(Lot.sku == sku, Lot.code == lot_code)
        .with_for_update()
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
    adjustment_direction: Optional[str],
    reason: str,
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
        return _handle_idempotent_replay(
            db,
            existing,
            sku,
            warehouse_id,
            lot_code,
            type_,
            quantity,
            adjustment_direction,
            reason,
        )

    # 2 — Validate existence
    article, warehouse, lot = _validate_existence(db, sku, warehouse_id, lot_code)

    # 3 — Inside transaction: check stock for salida
    reduces_stock = type_ == "salida" or (
        type_ == "ajuste" and adjustment_direction == "reducir"
    )
    if reduces_stock:
        current_stock = _stock_query(db, sku, warehouse_id, lot.id)[0][2]
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
        adjustment_direction=adjustment_direction,
        reason=reason,
        request_key=request_key,
        recorded_at=now,
    )
    db.add(movement)
    db.flush()

    # 5 — Compute resulting stock
    resulting_stock = _stock_query(db, sku, warehouse_id, lot.id)[0][2]

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
    adjustment_direction: Optional[str],
    reason: str,
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
        and existing.adjustment_direction == adjustment_direction
        and existing.reason == reason
    ):
        # Replay — reconstruct the original stock result
        # Sum only movements of that lot+warehouse up to the original sequence
        stmt = select(
            func.coalesce(
                func.sum(
                    case(
                        (Movement.type == "entrada", Movement.quantity),
                        (Movement.type == "salida", -Movement.quantity),
                        (
                            and_(
                                Movement.type == "ajuste",
                                Movement.adjustment_direction == "aumentar",
                            ),
                            Movement.quantity,
                        ),
                        else_=-Movement.quantity,
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
        adjustment_direction=m.adjustment_direction,
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

    if warehouse_id and db.get(Warehouse, warehouse_id) is None:
        raise ResourceNotFound(f"Warehouse '{warehouse_id}' not found")

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
    for lot_id_val, line_warehouse, stock, lot_code_val in rows:
        lines.append(
            StockLine(
                warehouse_id=line_warehouse,
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
        current_stock = sum(row[2] for row in rows)
        if article.active and current_stock <= article.reorder_point:
            items.append(
                ReorderItem(
                    sku=article.sku,
                    name=article.name,
                    reorder_point=article.reorder_point,
                    current_stock=current_stock,
                )
            )

    return ReorderResponse(items=items, total_below_reorder=len(items))