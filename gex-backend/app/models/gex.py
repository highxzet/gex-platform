"""gex_by_strike ve gex_summary tabloları — Build Spec Bölüm 5.5 / 5.6.

`gex_summary` Ana Panel ve İzleme Listesi'nin birincil veri kaynağıdır: sık okunur,
bu yüzden ayrı ve hafif tutulur. Zaman serisi olarak üzerine YAZILMAZ (Bölüm 3.10).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

REGIMES = ("positive", "negative", "neutral", "unknown")


class GexByStrike(Base):
    __tablename__ = "gex_by_strike"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    strike: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    expiry: Mapped[date] = mapped_column(Date, nullable=False)
    call_gex: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    put_gex: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    net_gex: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_gex_by_strike_symbol_run", "symbol_id", "calculation_run_id"),
        Index("idx_gex_by_strike_symbol_time", "symbol_id", computed_at.desc()),
    )


class GexSummary(Base):
    __tablename__ = "gex_summary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    total_net_gex: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    gamma_flip_strike: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    call_wall_strike: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    put_wall_strike: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    regime: Mapped[str] = mapped_column(String(10), nullable=False)
    spot_price_at_calc: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "regime IN ('positive', 'negative', 'neutral', 'unknown')",
            name="ck_gex_summary_regime",
        ),
        Index("idx_gex_summary_symbol_time", "symbol_id", computed_at.desc()),
    )
