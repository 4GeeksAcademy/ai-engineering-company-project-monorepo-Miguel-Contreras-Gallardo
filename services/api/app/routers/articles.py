"""CRUD endpoints for articles (SKU catalog) and lots."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models import Article, Lot, Movement
from app.schemas.inventory import ArticleCreate, ArticleResponse, ArticleUpdate, LotCreate, LotResponse

router = APIRouter(prefix="/articles", tags=["articles"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Create ──────────────────────────────────────────────────────────


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)):
    existing = db.get(Article, payload.sku)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Article SKU '{payload.sku}' already exists",
        )
    article = Article(**payload.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


# ── List ────────────────────────────────────────────────────────────


@router.get("/", response_model=List[ArticleResponse])
def list_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.sku).all()


# ── Get by SKU ──────────────────────────────────────────────────────


@router.get("/{sku}", response_model=ArticleResponse)
def get_article(sku: str, db: Session = Depends(get_db)):
    article = db.get(Article, sku)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article SKU '{sku}' not found",
        )
    return article


# ── Update ──────────────────────────────────────────────────────────


@router.put("/{sku}", response_model=ArticleResponse)
def update_article(sku: str, payload: ArticleUpdate, db: Session = Depends(get_db)):
    article = db.get(Article, sku)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article SKU '{sku}' not found",
        )
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    for field, value in update_data.items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return article


# ── Delete ──────────────────────────────────────────────────────────


@router.delete("/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(sku: str, db: Session = Depends(get_db)):
    article = db.get(Article, sku)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article SKU '{sku}' not found",
        )
    # Manually cascade: delete movements → lots → article
    # (avoids SQLite FK + ORM cascade conflicts; PostgreSQL can rely on FK CASCADE)
    lot_ids = [lot.id for lot in article.lots]
    if lot_ids:
        db.query(Movement).filter(Movement.lot_id.in_(lot_ids)).delete(
            synchronize_session=False
        )
    db.query(Lot).filter(Lot.sku == sku).delete(synchronize_session=False)
    db.delete(article)
    db.commit()
    return None


# ── Lots ─────────────────────────────────────────────────────────────


@router.post("/{sku}/lots", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(sku: str, payload: LotCreate, db: Session = Depends(get_db)):
    article = db.get(Article, sku)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article SKU '{sku}' not found",
        )
    existing = (
        db.query(Lot).filter(Lot.sku == sku, Lot.code == payload.code).first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lot code '{payload.code}' already exists for SKU '{sku}'",
        )
    lot = Lot(sku=sku, code=payload.code)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


@router.get("/{sku}/lots", response_model=List[LotResponse])
def list_lots(sku: str, db: Session = Depends(get_db)):
    article = db.get(Article, sku)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article SKU '{sku}' not found",
        )
    return db.query(Lot).filter(Lot.sku == sku).order_by(Lot.code).all()


@router.get("/{sku}/lots/{lot_code}", response_model=LotResponse)
def get_lot_by_code(sku: str, lot_code: str, db: Session = Depends(get_db)):
    lot = db.query(Lot).filter(Lot.sku == sku, Lot.code == lot_code).first()
    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lot code '{lot_code}' not found for SKU '{sku}'",
        )
    return lot