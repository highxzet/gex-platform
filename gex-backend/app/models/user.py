"""users tablosu — Build Spec Bölüm 5.8 (+ Bölüm 11.5 hesap kilitleme alanları)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # bcrypt/argon2 hash — asla düz metin (Bölüm 11.2)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    theme_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="dark")
    density_preference: Mapped[str] = mapped_column(
        String(10), nullable=False, default="standard"
    )
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Bölüm 11.5 — başarısız giriş sayacı / kilit
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "theme_preference IN ('dark', 'light', 'system')", name="ck_users_theme"
        ),
        CheckConstraint(
            "density_preference IN ('standard', 'compact')", name="ck_users_density"
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"
