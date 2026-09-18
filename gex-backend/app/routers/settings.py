"""Ayarlar endpoint'leri — Build Spec Bölüm 7.10 / 17.6 (KVKK/GDPR)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import AuthError, BusinessRuleError
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models import Alert, JournalEntry, Symbol, User, WatchlistItem
from app.schemas.alert import AppearanceUpdate, ChangePasswordRequest, ProfileUpdate
from app.schemas.auth import UserOut

router = APIRouter(prefix="/settings", tags=["Ayarlar"])


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/profile", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.patch("/appearance", response_model=UserOut)
def update_appearance(
    payload: AppearanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserOut:
    if payload.theme is not None:
        current_user.theme_preference = payload.theme
    if payload.density is not None:
        current_user.density_preference = payload.density
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.post("/change-password", status_code=204, response_class=Response)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise AuthError("INVALID_CREDENTIALS", "Mevcut şifre hatalı.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=204)


@router.get("/export-data")
def export_data(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict:
    """Kullanıcının tüm verisini indirilebilir JSON olarak döner (Bölüm 17.6 KVKK/GDPR)."""
    watchlist = db.execute(
        select(Symbol.ticker)
        .join(WatchlistItem, WatchlistItem.symbol_id == Symbol.id)
        .where(WatchlistItem.user_id == current_user.id)
    ).scalars().all()

    alerts = db.scalars(select(Alert).where(Alert.user_id == current_user.id)).all()
    entries = db.scalars(
        select(JournalEntry).where(JournalEntry.user_id == current_user.id)
    ).all()

    return {
        "profile": UserOut.model_validate(current_user).model_dump(mode="json"),
        "watchlist": list(watchlist),
        "alerts": [
            {
                "condition_type": a.condition_type,
                "threshold_value": float(a.threshold_value),
                "channels": list(a.channels or []),
                "enabled": a.enabled,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "journal": [
            {"content": e.content, "created_at": e.created_at.isoformat()} for e in entries
        ],
    }


@router.delete("/account", status_code=204, response_class=Response)
def delete_account(
    confirmation_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Hesabı ve ilişkili tüm veriyi siler (ON DELETE CASCADE — Bölüm 17.6)."""
    if confirmation_text != "SİL":
        raise BusinessRuleError("CONFIRMATION_MISMATCH", "Onay metni eşleşmiyor.")
    db.delete(current_user)
    db.commit()
    return Response(status_code=204)
