# services/api/app/main.py

"""
TrackFlow API — Entry point.

FastAPI application that serves the Incident Manager and future services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.database import Base, engine
from app.routers.incidents import router as incidents_router

# ── Create tables on startup (dev mode; production should use Alembic) ──────

Base.metadata.create_all(bind=engine)

# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="TrackFlow API",
    description="Backend centralizado para la plataforma TrackFlow "
                "(logística de última milla e IA)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allow dashboard from any origin ──────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files — serve UIs directly ───────────────────────────────────────

app.mount("/ui", StaticFiles(directory="../../uis", html=True), name="ui")

# ── Routers ─────────────────────────────────────────────────────────────────

app.include_router(incidents_router)


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "trackflow-api", "version": "0.1.0"}


@app.get("/healthz", tags=["health"])
def healthz():
    return {"status": "ok"}