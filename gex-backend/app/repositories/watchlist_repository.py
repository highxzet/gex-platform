"""İzleme listesi veri erişimi — Build Spec Bölüm 6.1 / 7.5."""
from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Symbol, WatchlistItem


def list_for_user(db: Session, user_id: uuid.UUID) -> list[tuple[WatchlistItem, Symbol]]:
    rows = db.execute(
        select(WatchlistItem, Symbol)
        .join(Symbol, Symbol.id == WatchlistItem.symbol_id)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.sort_order, Symbol.ticker)
    ).all()
    return [(r[0], r[1]) for r in rows]


def exists(db: Session, user_id: uuid.UUID, symbol_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(WatchlistItem.id).where(
                WatchlistItem.user_id == user_id, WatchlistItem.symbol_id == symbol_id
            )
        )
        is not None
    )


def add(db: Session, user_id: uuid.UUID, symbol_id: uuid.UUID) -> WatchlistItem:
    next_order = (
        db.scalar(
            select(func.coalesce(func.max(WatchlistItem.sort_order), -1)).where(
                WatchlistItem.user_id == user_id
            )
        )
        + 1
    )
    item = WatchlistItem(user_id=user_id, symbol_id=symbol_id, sort_order=next_order)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove(db: Session, user_id: uuid.UUID, symbol_id: uuid.UUID) -> int:
    result = db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.user_id == user_id, WatchlistItem.symbol_id == symbol_id
        )
    )
    db.commit()
    return result.rowcount or 0


def reorder(db: Session, user_id: uuid.UUID, ordered_symbol_ids: list[uuid.UUID]) -> None:
    for index, symbol_id in enumerate(ordered_symbol_ids):
        db.execute(
            WatchlistItem.__table__.update()
            .where(
                WatchlistItem.user_id == user_id,
                WatchlistItem.symbol_id == symbol_id,
            )
            .values(sort_order=index)
        )
    db.commit()
