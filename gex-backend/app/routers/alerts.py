"""Uyarı endpoint'leri — Build Spec Bölüm 7.6."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import ensure_owner, get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Alert, Symbol, User
from app.repositories import symbol_repository as sym_repo
from app.schemas.alert import AlertCreate, AlertListResponse, AlertOut, AlertUpdate

router = APIRouter(prefix="/alerts", tags=["Uyarılar"])


def _to_out(alert: Alert, ticker: str) -> AlertOut:
    return AlertOut(
        id=alert.id,
        symbol=ticker,
        condition_type=alert.condition_type,
        threshold_value=float(alert.threshold_value),
        channels=list(alert.channels or []),
        enabled=alert.enabled,
        last_triggered_at=alert.last_triggered_at,
        created_at=alert.created_at,
    )


def _get_owned_alert(db: Session, alert_id: uuid.UUID, current_user: User) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise NotFoundError("ALERT_NOT_FOUND", "Uyarı bulunamadı.")
    ensure_owner(alert.user_id, current_user, "uyarıya")
    return alert


@router.get("", response_model=AlertListResponse)
def list_alerts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> AlertListResponse:
    rows = db.execute(
        select(Alert, Symbol)
        .join(Symbol, Symbol.id == Alert.symbol_id)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
    ).all()
    return AlertListResponse(items=[_to_out(a, s.ticker) for a, s in rows])


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertOut:
    symbol = sym_repo.get_by_ticker(db, payload.symbol)
    if symbol is None:
        raise NotFoundError(
            "SYMBOL_NOT_FOUND", f"'{payload.symbol.upper()}' sembolü bulunamadı veya izleme listenizde değil."
        )
    alert = Alert(
        user_id=current_user.id,
        symbol_id=symbol.id,
        condition_type=payload.condition_type,
        threshold_value=payload.threshold_value,
        channels=list(payload.channels),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _to_out(alert, symbol.ticker)


@router.patch("/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertOut:
    alert = _get_owned_alert(db, alert_id, current_user)
    if payload.threshold_value is not None:
        alert.threshold_value = payload.threshold_value
    if payload.enabled is not None:
        alert.enabled = payload.enabled
    if payload.channels is not None:
        alert.channels = list(payload.channels)
    db.commit()
    db.refresh(alert)
    symbol = db.get(Symbol, alert.symbol_id)
    return _to_out(alert, symbol.ticker if symbol else "")


@router.delete("/{alert_id}", status_code=204, response_class=Response)
def delete_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    alert = _get_owned_alert(db, alert_id, current_user)
    db.delete(alert)
    db.commit()
    return Response(status_code=204)
