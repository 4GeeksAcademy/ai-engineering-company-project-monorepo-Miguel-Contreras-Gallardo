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

from app.routers.incidents import router as incidents_router
from app.routers.telemetry import router as telemetry_router

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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.mount("/ui", StaticFiles(directory=UI_DIRECTORY, html=True), name="ui")

    application.include_router(incidents_router)
    application.include_router(telemetry_router)
    application.include_router(articles.router)
    application.include_router(inventory.router)

    @application.get("/", tags=["health"])
    def health_check():
        return {"status": "ok", "service": "trackflow-api", "version": "0.1.0"}

    @application.get("/healthz", tags=["health"])
    def healthz():
        return {"status": "ok"}

    return application


app = create_app()
