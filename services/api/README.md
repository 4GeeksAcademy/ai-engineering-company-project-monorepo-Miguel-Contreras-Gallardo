# TrackFlow inventory API

FastAPI service backed by PostgreSQL. Stock is derived from the append-only
movement ledger; schema creation and initial warehouse data are owned by
Alembic migrations.

The API exposes article lifecycle management, lots, immutable entry/output/
adjustment movements, stock queries and reorder signals. Article deletion is a
logical deactivation and never removes ledger history.

## Local setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://trackflow:trackflow@localhost:5432/trackflow
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

The database and `trackflow` role must exist before applying the migration.

Run the focused test suite with:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```