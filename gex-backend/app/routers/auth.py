"""Kimlik doğrulama endpoint'leri — Build Spec Bölüm 7.2."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import AuthError
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.database import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    UserOut,
)
from app.services.auth_service import attempt_login

router = APIRouter(prefix="/auth", tags=["Kimlik Doğrulama"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = attempt_login(db, payload.email, payload.password)
    return LoginResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id), payload.remember_me),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(payload: RefreshRequest) -> RefreshResponse:
    claims = decode_token(payload.refresh_token)
    if claims.get("type") != "refresh":
        raise AuthError("TOKEN_INVALID", "Geçersiz token türü.")
    return RefreshResponse(access_token=create_access_token(str(claims["sub"])))


@router.post("/logout", status_code=204, response_class=Response)
def logout(_: User = Depends(get_current_user)) -> Response:
    """Kısa ömürlü access token stratejisi: istemci token'ı siler.

    (Sunucu tarafı blacklist Faz 3'te eklenebilir — Bölüm 11.3.)
    """
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
