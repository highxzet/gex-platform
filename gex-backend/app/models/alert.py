"""alerts tablosu — Build Spec Bölüm 5.10."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

CONDITION_TYPES = ("flip_distance", "regime_change", "gex_pct_change", "price_level")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    condition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    channels: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=lambda: ["in_app"]
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "condition_type IN ('flip_distance', 'regime_change', 'gex_pct_change', 'price_level')",
            name="ck_alerts_condition_type",
        ),
        Index("idx_alerts_user", "user_id"),
        Index("idx_alerts_enabled_symbol", "symbol_id", postgresql_where=(enabled.is_(True))),
    )
