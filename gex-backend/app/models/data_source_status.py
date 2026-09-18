"""data_source_status tablosu — Build Spec Bölüm 5.7.

Veri kaynağı sağlığını izler (Veri Durumu sayfasının backend karşılığı).
Sembole bağlı değil — sistem geneli.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

STATUSES = ("healthy", "degraded", "down")


class DataSourceStatus(Base):
    __tablename__ = "data_source_status"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('healthy', 'degraded', 'down')", name="ck_data_source_status"
        ),
        Index("idx_data_source_status_source_time", "source_name", checked_at.desc()),
    )
