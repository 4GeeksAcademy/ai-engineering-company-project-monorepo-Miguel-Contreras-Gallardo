# Reglas de testing

## Framework
- Usar **pytest** como framework de testing
- Usar **httpx.AsyncClient** para tests de API (con `TestClient` de Starlette)
- Tests de base de datos contra PostgreSQL real (no SQLite) — SQLite no reproduce row-level locking

## Estructura
- Tests en `services/api/tests/`
- Un archivo por módulo: `test_inventory.py`, `test_articles.py`, `test_movements.py`
- Tests de integración en `tests/integration/`

## Cobertura mínima
- Tests unitarios para servicios (lógica de dominio)
- Tests de integración para endpoints REST
- Tests de concurrencia (dos requests simultáneos)
- Tests de idempotencia (misma request_key)
- Tests de casos borde (SKU inexistente, stock insuficiente, tipos inválidos)

## Convenciones
- Nombrar tests con formato: `test_[funcionalidad]_[escenario]`
  ```python
  async def test_create_movement_insufficient_stock():
  async def test_get_stock_with_warehouse_filter():
  async def test_concurrent_withdrawals_only_one_succeeds():
  ```
- Usar fixtures de pytest para setup de DB y datos de prueba
- Marcar tests de integración con `@pytest.mark.integration`
- Tests de concurrencia usar `asyncio.gather()` o threads

## Fixtures recomendadas
```python
@pytest.fixture
async def db_session():
    # setup DB connection, create tables, yield session, teardown

@pytest.fixture
async def test_article(db_session):
    # create and return a test article

@pytest.fixture
async def test_lot(db_session, test_article):
    # create and return a test lot for the test article
```