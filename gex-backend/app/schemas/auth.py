"""Kimlik doğrulama şemaları — Build Spec Bölüm 7.2."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)
    remember_me: bool = False


class UserOut(BaseModel):
    """API'ye dönen kullanıcı — `password_hash` BİLİNÇLİ olarak yoktur (Bölüm 11.2)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str | None = None
    theme_preference: str = "dark"
    density_preference: str = "standard"
    onboarding_completed: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
