"""Uyarı, bildirim, günlük ve ayar şemaları — Build Spec Bölüm 7.6-7.8, 7.10."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ConditionType = Literal["flip_distance", "regime_change", "gex_pct_change", "price_level"]


# ---------- Uyarılar ----------
class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    condition_type: ConditionType
    threshold_value: float
    channels: list[Literal["in_app", "email"]] = Field(default_factory=lambda: ["in_app"])


class AlertUpdate(BaseModel):
    threshold_value: float | None = None
    enabled: bool | None = None
    channels: list[Literal["in_app", "email"]] | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    condition_type: str
    threshold_value: float
    channels: list[str]
    enabled: bool
    last_triggered_at: datetime | None = None
    created_at: datetime


class AlertListResponse(BaseModel):
    items: list[AlertOut]


# ---------- Bildirimler ----------
class NotificationOut(BaseModel):
    id: uuid.UUID
    message: str
    symbol: str | None = None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    unread_count: int


# ---------- Günlük ----------
class JournalCreate(BaseModel):
    symbol: str | None = None
    content: str = Field(min_length=1, max_length=10_000)


class JournalUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10_000)


class JournalOut(BaseModel):
    id: uuid.UUID
    symbol: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime


class JournalListResponse(BaseModel):
    items: list[JournalOut]


# ---------- Ayarlar ----------
class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)


class AppearanceUpdate(BaseModel):
    theme: Literal["dark", "light", "system"] | None = None
    density: Literal["standard", "compact"] | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=200)
