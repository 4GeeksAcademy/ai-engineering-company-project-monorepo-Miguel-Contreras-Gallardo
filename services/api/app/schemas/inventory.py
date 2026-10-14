"""Pydantic schemas for the inventory manager — request/response models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Helpers ──────────────────────────────────────────────────────────

class MovementType(str, Enum):
    entrada = "entrada"
    salida = "salida"
    ajuste = "ajuste"


class AdjustmentDirection(str, Enum):
    aumentar = "aumentar"
    reducir = "reducir"


# ── Articles ─────────────────────────────────────────────────────────

class ArticleCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reorder_point: int = Field(default=0, ge=0)


class ArticleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    reorder_point: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class ArticleResponse(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    reorder_point: int
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Warehouses ──────────────────────────────────────────────────────

class WarehouseCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = None


class WarehouseResponse(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Lots ─────────────────────────────────────────────────────────────

class LotCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)


class LotResponse(BaseModel):
    id: int
    sku: str
    code: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Movements ────────────────────────────────────────────────────────

class MovementRegister(BaseModel):
    sku: str = Field(..., min_length=1)
    warehouse_id: str = Field(..., min_length=1)
    lot_code: str = Field(..., min_length=1)
    type: MovementType
    quantity: int = Field(..., gt=0)
    adjustment_direction: Optional[AdjustmentDirection] = None
    reason: str = Field(..., min_length=1, max_length=500)
    request_key: str = Field(..., min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_adjustment_direction(self):
        if self.type == MovementType.ajuste and self.adjustment_direction is None:
            raise ValueError("adjustment_direction is required for ajuste movements")
        if self.type != MovementType.ajuste and self.adjustment_direction is not None:
            raise ValueError("adjustment_direction is only valid for ajuste movements")
        return self


class MovementResponse(BaseModel):
    id: int
    sequence: int
    sku: str
    warehouse_id: str
    lot_id: int
    type: str
    quantity: int
    adjustment_direction: Optional[str] = None
    reason: str
    recorded_at: datetime

    model_config = {"from_attributes": True}


class MovementResult(BaseModel):
    """Returned after registering a movement — includes resulting stock."""

    movement: MovementResponse
    resulting_stock: int


# ── Stock queries ────────────────────────────────────────────────────

class StockLine(BaseModel):
    warehouse_id: str
    lot_id: int
    lot_code: str
    stock: int


class StockQueryResponse(BaseModel):
    sku: str
    lines: List[StockLine]
    total: int


# ── Reorder signal ──────────────────────────────────────────────────

class ReorderItem(BaseModel):
    sku: str
    name: str
    reorder_point: int
    current_stock: int


class ReorderResponse(BaseModel):
    items: List[ReorderItem]
    total_below_reorder: int