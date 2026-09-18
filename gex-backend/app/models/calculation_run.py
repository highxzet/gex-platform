"""calculation_runs tablosu — Build Spec Bölüm 5.13.

Her hesaplama döngüsünün meta verisi: denetim/izlenebilirlik ve şeffaflık için.
`calculation_run_id` sayesinde her çalıştırma ayrı bir kayıt seti üretir (idempotency, Bölüm 21.2).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

RUN_STATUSES = ("running", "completed", "failed")


class CalculationRun(Base):
    __tablename__ = "calculation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    symbols_succeeded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbols_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed')", name="ck_calculation_runs_status"
        ),
    )
