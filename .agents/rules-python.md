# Reglas de desarrollo Python / FastAPI

## Estilo y estructura
- Seguir **PEP 8** (máx. 88 caracteres por línea — compatible con Black)
- Usar **type hints** en todas las funciones y métodos
- Documentar con **docstrings** estilo Google:
  ```python
  def get_stock(sku: str, warehouse_id: int | None = None) -> StockResult:
      """Get current stock for a SKU, optionally filtered by warehouse.
      
      Args:
          sku: The SKU to query.
          warehouse_id: Optional warehouse filter.
      
      Returns:
          StockResult with per-lot details and total.
      
      Raises:
          NotFoundError: If SKU or warehouse doesn't exist.
      """
  ```

## FastAPI
- Usar **Pydantic v2** para schemas de request/response
- Los routers solo validan formato y traducen errores de dominio
- La lógica de dominio vive en `services/`, nunca en `routers/`
- Endpoints REST con nombres en plural: `/api/v1/articles`, `/api/v1/movements`
- Códigos HTTP semánticos: 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 409 Conflict

## SQLAlchemy
- Usar modelos con `Mapped` y `mapped_column` (SQLAlchemy 2.0 style)
- Relaciones explícitas con `relationship()` y `ForeignKey`
- Transacciones con `Session` context manager
- Queries raw SQL para consultas de stock (no ORM para agregaciones)

## Dependencias
- `requirements.txt` para producción
- `requirements-dev.txt` para desarrollo (pytest, httpx, black, ruff)
- Usar virtualenv en `.venv/`