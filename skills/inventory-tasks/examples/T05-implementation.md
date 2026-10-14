# Ejemplo: Implementar T05 — Validación de entrada de movimientos

## Contexto

T05 requiere validar en la capa de entrada: tipo, cantidad entera positiva y almacén existente antes de registrar movimientos (INV-008).

## Código

### Schema Pydantic (services/api/app/schemas/inventory.py)

```python
from enum import Enum
from pydantic import BaseModel, Field, PositiveInt

class MovementType(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"

class MovementCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    warehouse_id: int = Field(..., gt=0)
    lot_id: int = Field(..., gt=0)
    type: MovementType
    quantity: PositiveInt
    request_key: str = Field(..., min_length=1, max_length=100)
```

### Test (services/api/tests/test_movements.py)

```python
async def test_create_movement_invalid_type_returns_error(async_client):
    response = await async_client.post("/api/v1/movements", json={
        "sku": "SKU001",
        "warehouse_id": 1,
        "lot_id": 1,
        "type": "invalido",
        "quantity": 10,
        "request_key": "req-001"
    })
    assert response.status_code == 422
    assert "type" in response.text
```

## Verificación

```bash
cd services/api && pytest tests/test_movements.py -v -k "invalid"
```