# services/api/app/main.py

"""
TrackFlow API — Entry point.

FastAPI application that serves the Incident Manager, Inventory Manager,
and future services.
"""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.incidents import router as incidents_router
from app.routers.telemetry import router as telemetry_router
from app.schemas.health import HealthResponse

# Import inventory routers
from app.routers import articles, inventory

logger = logging.getLogger("api.timing")
UI_DIRECTORY = Path(__file__).resolve().parents[3] / "uis"


def create_app() -> FastAPI:
    """Create an API application instance for production or isolated tests."""
    application = FastAPI(
        title="TrackFlow API",
        description="Backend centralizado para la plataforma TrackFlow "
                    "(logística de última milla e IA)",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @application.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %s | %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response

    application.add_middleware(
        CORSMiddleware,
        # Fallback CORS: cuando el frontend no pasa por el proxy (p.ej. llamadas
        # directas desde :3001 o desde una URL forwardeada de GitHub Codespaces).
        allow_origins=settings.cors_origins
        if settings.cors_origins
        else ["http://localhost:3001", "http://localhost:5173", "http://127.0.0.1:3001", "http://127.0.0.1:5173"],
        allow_origin_regex=r"^https://.*\.app\.github\.dev$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    application.mount("/ui", StaticFiles(directory=UI_DIRECTORY, html=True), name="ui")

    application.include_router(incidents_router)
    application.include_router(telemetry_router)
    application.include_router(articles.router)
    application.include_router(inventory.router)

    # Alias bajo /api para que las rutas RELATIVAS del frontend (/api/articles/,
    # /api/inventory/*, /api/telemetry/events) también existan cuando el frontend
    # se sirve desde el propio FastAPI (mount /ui, puerto 8000) sin proxy.
    # NO se re-incluye incidents_router: su prefijo ya es /api/v1/incidents.
    application.include_router(telemetry_router, prefix="/api")
    application.include_router(articles.router, prefix="/api")
    application.include_router(inventory.router, prefix="/api")

    @application.get("/", response_model=HealthResponse, tags=["health"])
    def health_check():
        return {"status": "ok", "service": "trackflow-api", "version": "0.1.0"}

    @application.get("/healthz", response_model=HealthResponse, tags=["health"])
    def healthz():
        return HealthResponse(status="ok", service="trackflow-api", version="0.1.0")

    return application


app = create_app()
