"""Kimlik doğrulama yardımcıları — JWT + şifre hashleme (Build Spec Bölüm 11).

Not: `get_current_user` dependency'si, users modeli hazır olduğunda (Faz 4)
routers/auth.py ile birlikte etkinleşir. Skeleton'da token üretme/doğrulama
fonksiyonları hazır ve test edilebilir.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings
from app.core.exceptions import AuthError

ALGORITHM = "HS256"

# bcrypt 72 baytın üzerini yok sayar; belirsiz davranış yerine açıkça kısaltıyoruz.
_BCRYPT_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


# ---- Şifre (Bölüm 11.2) ----
def hash_password(plain_password: str) -> str:
    """bcrypt hash üretir. Düz metin asla saklanmaz/loglanmaz."""
    return bcrypt.hashpw(_encode(plain_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Hash doğrular. Bozuk/geçersiz hash'te istisna fırlatmaz, False döner."""
    try:
        return bcrypt.checkpw(_encode(plain_password), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---- Token (Bölüm 11.3) ----
def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, remember_me: bool = False) -> str:
    days = (
        settings.refresh_token_expire_days_remember_me
        if remember_me
        else settings.refresh_token_expire_days
    )
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=days),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("TOKEN_EXPIRED", "Oturumunuzun süresi doldu, tekrar giriş yapın.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("TOKEN_INVALID", "Geçersiz oturum.") from exc
