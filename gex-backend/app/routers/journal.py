"""Günlük (journal) endpoint'leri — Build Spec Bölüm 7.8."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import ensure_owner, get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import JournalEntry, Symbol, User
from app.repositories import symbol_repository as sym_repo
from app.schemas.alert import JournalCreate, JournalListResponse, JournalOut, JournalUpdate

router = APIRouter(prefix="/journal", tags=["Günlük"])


def _to_out(entry: JournalEntry, ticker: str | None) -> JournalOut:
    return JournalOut(
        id=entry.id,
        symbol=ticker,
        content=entry.content,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _get_owned_entry(db: Session, entry_id: uuid.UUID, current_user: User) -> JournalEntry:
    entry = db.get(JournalEntry, entry_id)
    if entry is None:
        raise NotFoundError("JOURNAL_NOT_FOUND", "Not bulunamadı.")
    ensure_owner(entry.user_id, current_user, "nota")
    return entry


@router.get("", response_model=JournalListResponse)
def list_entries(
    symbol: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalListResponse:
    stmt = (
        select(JournalEntry, Symbol)
        .outerjoin(Symbol, Symbol.id == JournalEntry.symbol_id)
        .where(JournalEntry.user_id == current_user.id)
    )
    if symbol:
        found = sym_repo.get_by_ticker(db, symbol)
        if found is None:
            return JournalListResponse(items=[])
        stmt = stmt.where(JournalEntry.symbol_id == found.id)

    rows = db.execute(stmt.order_by(JournalEntry.created_at.desc())).all()
    return JournalListResponse(items=[_to_out(e, s.ticker if s else None) for e, s in rows])


@router.post("", response_model=JournalOut, status_code=201)
def create_entry(
    payload: JournalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalOut:
    symbol_id = None
    ticker = None
    if payload.symbol:
        symbol = sym_repo.get_by_ticker(db, payload.symbol)
        if symbol is None:
            raise NotFoundError(
                "SYMBOL_NOT_FOUND", f"'{payload.symbol.upper()}' sembolü bulunamadı veya izleme listenizde değil."
            )
        symbol_id = symbol.id
        ticker = symbol.ticker

    entry = JournalEntry(user_id=current_user.id, symbol_id=symbol_id, content=payload.content)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _to_out(entry, ticker)


@router.patch("/{entry_id}", response_model=JournalOut)
def update_entry(
    entry_id: uuid.UUID,
    payload: JournalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JournalOut:
    entry = _get_owned_entry(db, entry_id, current_user)
    entry.content = payload.content
    db.commit()
    db.refresh(entry)
    symbol = db.get(Symbol, entry.symbol_id) if entry.symbol_id else None
    return _to_out(entry, symbol.ticker if symbol else None)


@router.delete("/{entry_id}", status_code=204, response_class=Response)
def delete_entry(
    entry_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    entry = _get_owned_entry(db, entry_id, current_user)
    db.delete(entry)
    db.commit()
    return Response(status_code=204)
