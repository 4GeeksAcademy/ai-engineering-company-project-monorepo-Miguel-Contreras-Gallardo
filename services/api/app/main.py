"""FastAPI application entry point."""

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import Base, engine, SessionLocal
from app.db.models import Article, Lot, Movement, Warehouse
from app.routers import articles, inventory


def _seed_warehouses():
    """Insert the two initial warehouses if they don't exist yet."""
    db: Session = SessionLocal()
    try:
        for wh_id, name, loc in [
            ("LAX", "Los Angeles Warehouse", "Los Angeles, USA"),
            ("ZAZ", "Zaragoza Warehouse", "Zaragoza, Spain"),
        ]:
            existing = db.get(Warehouse, wh_id)
            if existing is None:
                db.add(Warehouse(id=wh_id, name=name, location=loc))
        db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    _seed_warehouses()

    app = FastAPI(
        title="TrackFlow Inventory Manager",
        version="0.1.0",
        description="Unified inventory API — stock derived from movement ledger",
    )

    app.include_router(articles.router)
    app.include_router(inventory.router)

    return app


app = create_app()