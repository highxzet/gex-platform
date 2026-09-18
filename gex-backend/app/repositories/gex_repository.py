"""GEX veri erişimi — Build Spec Bölüm 5.6 / 6.1.

Repository katmanı İŞ MANTIĞI İÇERMEZ; yalnızca sorgu/CRUD (Bölüm 6.1 kuralı).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models import GexByStrike, GexSummary, OptionChainRaw, PriceSnapshot, Symbol


def _latest_summary_stmt(symbol_ids: list[uuid.UUID]) -> Select:
    """Her sembol için EN GÜNCEL gex_summary satırı (Bölüm 5.6 DISTINCT ON).

    N+1 sorgu problemini önler (Bölüm 18.1).
    """
    return (
        select(GexSummary)
        .where(GexSummary.symbol_id.in_(symbol_ids))
        .distinct(GexSummary.symbol_id)
        .order_by(GexSummary.symbol_id, desc(GexSummary.computed_at))
    )


def get_latest_summaries(db: Session, symbol_ids: list[uuid.UUID]) -> dict[uuid.UUID, GexSummary]:
    if not symbol_ids:
        return {}
    rows = db.scalars(_latest_summary_stmt(symbol_ids)).all()
    return {r.symbol_id: r for r in rows}


def get_latest_summary(db: Session, symbol_id: uuid.UUID) -> GexSummary | None:
    return db.scalar(
        select(GexSummary)
        .where(GexSummary.symbol_id == symbol_id)
        .order_by(desc(GexSummary.computed_at))
        .limit(1)
    )


def get_previous_summary(
    db: Session, symbol_id: uuid.UUID, before: datetime
) -> GexSummary | None:
    """Alert engine için: verilen andan önceki en güncel özet (Bölüm 12.2)."""
    return db.scalar(
        select(GexSummary)
        .where(GexSummary.symbol_id == symbol_id, GexSummary.computed_at < before)
        .order_by(desc(GexSummary.computed_at))
        .limit(1)
    )


def get_summary_history(
    db: Session, symbol_id: uuid.UUID, days: int
) -> list[GexSummary]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return list(
        db.scalars(
            select(GexSummary)
            .where(GexSummary.symbol_id == symbol_id, GexSummary.computed_at >= cutoff)
            .order_by(GexSummary.computed_at)
        )
    )


def get_strikes_for_run(
    db: Session, symbol_id: uuid.UUID, run_id: uuid.UUID
) -> list[GexByStrike]:
    return list(
        db.scalars(
            select(GexByStrike)
            .where(
                GexByStrike.symbol_id == symbol_id,
                GexByStrike.calculation_run_id == run_id,
            )
            .order_by(GexByStrike.strike)
        )
    )


def get_latest_price(db: Session, symbol_id: uuid.UUID) -> PriceSnapshot | None:
    return db.scalar(
        select(PriceSnapshot)
        .where(PriceSnapshot.symbol_id == symbol_id)
        .order_by(desc(PriceSnapshot.fetched_at))
        .limit(1)
    )


def get_latest_prices(db: Session, symbol_ids: list[uuid.UUID]) -> dict[uuid.UUID, PriceSnapshot]:
    if not symbol_ids:
        return {}
    rows = db.scalars(
        select(PriceSnapshot)
        .where(PriceSnapshot.symbol_id.in_(symbol_ids))
        .distinct(PriceSnapshot.symbol_id)
        .order_by(PriceSnapshot.symbol_id, desc(PriceSnapshot.fetched_at))
    ).all()
    return {r.symbol_id: r for r in rows}


def get_raw_chain_page(
    db: Session, symbol_id: uuid.UUID, page: int, page_size: int
) -> tuple[list[OptionChainRaw], int]:
    """Ham veri sekmesi için sayfalanmış sorgu (Bölüm 7.4)."""
    latest = db.scalar(
        select(OptionChainRaw.fetched_at)
        .where(OptionChainRaw.symbol_id == symbol_id)
        .order_by(desc(OptionChainRaw.fetched_at))
        .limit(1)
    )
    if latest is None:
        return [], 0

    base = select(OptionChainRaw).where(
        OptionChainRaw.symbol_id == symbol_id, OptionChainRaw.fetched_at == latest
    )
    total = len(db.scalars(base).all())
    rows = list(
        db.scalars(
            base.order_by(OptionChainRaw.expiry, OptionChainRaw.strike)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return rows, total


def get_sparkline(db: Session, symbol_id: uuid.UUID, points: int = 7) -> list[float]:
    """Son N hesaplamanın net GEX'i (milyar $ cinsinden, grafik için)."""
    rows = db.scalars(
        select(GexSummary.total_net_gex)
        .where(GexSummary.symbol_id == symbol_id)
        .order_by(desc(GexSummary.computed_at))
        .limit(points)
    ).all()
    return [float(v) / 1e9 for v in reversed(rows)]


def get_active_symbols(db: Session) -> list[Symbol]:
    return list(db.scalars(select(Symbol).where(Symbol.is_active.is_(True)).order_by(Symbol.ticker)))
