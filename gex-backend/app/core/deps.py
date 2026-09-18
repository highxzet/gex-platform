"""FastAPI bağımlılıkları (DI) — Build Spec Bölüm 6.4 / 11.4.

`security.py`'den ayrı tutulur: orası saf token/şifre mantığıdır (DB bilmez),
burası ise DB ve model katmanına bağlanır.
"""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ForbiddenError, NotFoundError
from app.core.security import decode_token
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("NOT_AUTHENTICATED", "Bu işlem için giriş yapmalısınız.")

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise AuthError("TOKEN_INVALID", "Geçersiz token türü.")

    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise AuthError("TOKEN_INVALID", "Geçersiz oturum.") from exc

    user = db.get(User, user_id)
    if user is None:
        raise AuthError("TOKEN_INVALID", "Kullanıcı bulunamadı.")
    return user


def ensure_owner(resource_user_id: uuid.UUID, current_user: User, label: str = "kaynağa") -> None:
    """Kaynak sahipliği kontrolü — Bölüm 11.6 / 17.2.

    Kimlik doğrulaması TEK BAŞINA yeterli değildir; kaynağın gerçekten o
    kullanıcıya ait olduğu her zaman doğrulanır.
    """
    if resource_user_id != current_user.id:
        raise ForbiddenError("FORBIDDEN", f"Bu {label} erişim yetkiniz yok.")


def not_found(code: str, message: str) -> NotFoundError:
    return NotFoundError(code, message)
