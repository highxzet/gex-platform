"""symbols tablosu — Build Spec Bölüm 5.2."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    company_name: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(100))
    # Endeks üyeliği: "SP500", "NDX" veya "NDX+SP500" (evren filtrelemesi için)
    indices: Mapped[str | None] = mapped_column(String(20))
    has_options_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_symbols_ticker", "ticker"),
        Index("idx_symbols_indices", "indices"),
        Index(
            "idx_symbols_active",
            "is_active",
            postgresql_where=(is_active.is_(True)),
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Symbol {self.ticker}>"
