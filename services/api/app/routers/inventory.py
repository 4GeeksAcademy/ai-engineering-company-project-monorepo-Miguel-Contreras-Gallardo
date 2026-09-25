"""Endpoints for registering and querying inventory movements."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.schemas.inventory import (
    MovementRegister,
    MovementResult,
    MovementResponse,
    ReorderResponse,
    StockQueryResponse,
)
from app.services.inventory import (
    ConflictRequestKey,
    InsufficientStock,
    ResourceNotFound,
    get_reorder_items,
    query_stock,
    register_movement,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Register movement ───────────────────────────────────────────────


@router.post("/movements", response_model=MovementResult, status_code=status.HTTP_201_CREATED)
def create_movement(payload: MovementRegister, db: Session = Depends(get_db)):
    try:
        result = register_movement(
            db,
            sku=payload.sku,
            warehouse_id=payload.warehouse_id,
            lot_code=payload.lot_code,
            type_=payload.type.value,
            quantity=payload.quantity,
            reason=payload.reason,
            request_key=payload.request_key,
        )
        db.commit()
        return result
    except ResourceNotFound as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InsufficientStock as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ConflictRequestKey as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        # e.g. lot_code without warehouse_id
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        db.rollback()
        raise


# ── Replay oriented: also GET for idempotency inspection is fine
@router.get("/movements", response_model=MovementResult)
def get_movement_by_request_key(request_key: str, db: Session = Depends(get_db)):
    from app.db.models import Movement

    movement = db.query(Movement).filter(Movement.request_key == request_key).first()
    if movement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No movement found for request key '{request_key}'",
        )
    from app.services.inventory import _movement_to_response, _stock_query

    resulting_stock = _stock_query(db, movement.sku, movement.warehouse_id, movement.lot_id)
    stock_val = resulting_stock[0][1] if resulting_stock else 0
    return MovementResult(
        movement=_movement_to_response(movement),
        resulting_stock=stock_val,
    )


# ── Stock query ─────────────────────────────────────────────────────


@router.get("/stock", response_model=StockQueryResponse)
def get_stock(
    sku: str,
    warehouse_id: Optional[str] = None,
    lot_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        return query_stock(db, sku, warehouse_id, lot_code)
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Reorder signal ──────────────────────────────────────────────────


@router.get("/reorder", response_model=ReorderResponse)
def reorder_signal(db: Session = Depends(get_db)):
    return get_reorder_items(db)