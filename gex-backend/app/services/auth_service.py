"""Kimlik doğrulama iş mantığı — Build Spec Bölüm 11.5."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import AuthError
from app.core.security import verify_password
from app.models import User


def attempt_login(db: Session, email: str, password: str) -> User:
    """Giriş dener; başarısız denemeleri sayar ve eşiği aşınca hesabı kilitler.

    Kullanıcı numaralandırma saldırısını önlemek için "kullanıcı yok" ve
    "şifre yanlış" durumları AYNI hatayı döndürür (Bölüm 11.5 / 17.2).
    """
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None:
        raise AuthError("INVALID_CREDENTIALS", "E-posta veya şifre hatalı.")

    now = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now:
        raise AuthError(
            "ACCOUNT_LOCKED",
            f"Çok fazla başarısız deneme. {settings.lockout_minutes} dakika sonra tekrar deneyin.",
        )

    if not verify_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= settings.max_failed_login_attempts:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
        db.commit()
        raise AuthError("INVALID_CREDENTIALS", "E-posta veya şifre hatalı.")

    # Başarılı giriş — sayaç sıfırlanır
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)
    return user
