"""Sembol veri erişimi — Build Spec Bölüm 6.1."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Symbol


def get_by_ticker(db: Session, ticker: str) -> Symbol | None:
    return db.scalar(select(Symbol).where(Symbol.ticker == ticker.upper()))


def get_by_id(db: Session, symbol_id: uuid.UUID) -> Symbol | None:
    return db.get(Symbol, symbol_id)


def search(db: Session, query: str, limit: int = 20) -> list[Symbol]:
    """Ticker veya şirket adına göre arama (Bölüm 7.4).

    ORM/parametreli sorgu kullanılır — SQL enjeksiyonu riski yok (Bölüm 17.3).
    """
    like = f"%{query.strip()}%"
    return list(
        db.scalars(
            select(Symbol)
            .where(
                Symbol.is_active.is_(True),
                or_(Symbol.ticker.ilike(like), Symbol.company_name.ilike(like)),
            )
            .order_by(Symbol.ticker)
            .limit(limit)
        )
    )
