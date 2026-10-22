"""MVP Backend — FastAPI app with a single /status endpoint."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

app = FastAPI(title="MVP Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://mvp:mvp@localhost:5432/mvp",
)


def _check_db() -> bool:
    """Return True if PostgreSQL is reachable, False otherwise."""
    try:
        # psycopg2 expects postgresql:// not postgresql+psycopg://
        dsn = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
        conn = psycopg2.connect(dsn, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


@app.get("/status")
def status():
    db_ok = _check_db()
    return {
        "status": "ok",
        "database": "connected" if db_ok else "unreachable",
    }