"""option_chain_raw tablosu — Build Spec Bölüm 5.4.

Ham, işlenmemiş opsiyon zinciri verisi: denetim / hata ayıklama / yeniden hesaplama için.
Hızla büyür → retention politikası Bölüm 5.15 / cleanup_job.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OptionChainRaw(Base):
    __tablename__ = "option_chain_raw"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("symbols.id", ondelete="CASCADE"), nullable=False
    )
    strike: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    expiry: Mapped[date] = mapped_column(Date, nullable=False)
    call_oi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    put_oi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    call_gamma: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    put_gamma: Mapped[Decimal | None] = mapped_column(Numeric(12, 8))
    # NUMERIC(12,6): sağlayıcıdan gelen aşırı IV değerleri taşmaya yol açmasın
    call_iv: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    put_iv: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_option_chain_symbol_time", "symbol_id", fetched_at.desc()),
        Index("idx_option_chain_symbol_strike_expiry", "symbol_id", "strike", "expiry"),
    )
