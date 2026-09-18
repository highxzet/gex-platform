"""Bildirim endpoint'leri — Build Spec Bölüm 7.7."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import ensure_owner, get_current_user
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models import Notification, Symbol, User
from app.schemas.alert import NotificationListResponse, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Bildirimler"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    stmt = (
        select(Notification, Symbol)
        .outerjoin(Symbol, Symbol.id == Notification.related_symbol_id)
        .where(Notification.user_id == current_user.id)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    rows = db.execute(stmt.order_by(Notification.created_at.desc()).limit(200)).all()

    unread_count = db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
    )

    return NotificationListResponse(
        items=[
            NotificationOut(
                id=n.id,
                message=n.message,
                symbol=s.ticker if s else None,
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n, s in rows
        ],
        unread_count=unread_count or 0,
    )


@router.patch("/read-all", status_code=204, response_class=Response)
def mark_all_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Response:
    db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return Response(status_code=204)


@router.patch("/{notification_id}/read", status_code=204, response_class=Response)
def mark_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise NotFoundError("NOTIFICATION_NOT_FOUND", "Bildirim bulunamadı.")
    ensure_owner(notification.user_id, current_user, "bildirime")
    notification.is_read = True
    db.commit()
    return Response(status_code=204)
