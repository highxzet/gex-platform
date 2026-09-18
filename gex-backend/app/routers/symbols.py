"""Sembol / Hisse Detay endpoint'leri — Build Spec Bölüm 7.4."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.database import get_db
from app.models import User
from app.repositories import gex_repository as gex_repo
from app.repositories import symbol_repository as sym_repo
from app.repositories import watchlist_repository as wl_repo
from app.schemas.gex import (
    GexProfileResponse,
    GexStrikePoint,
    RawDataResponse,
    RawDataRow,
    TimeSeriesPoint,
    TimeSeriesResponse,
)
from app.schemas.watchlist import SymbolSearchItem, SymbolSearchResponse

router = APIRouter(prefix="/symbols", tags=["Semboller"])

RANGE_DAYS = {"7d": 7, "30d": 30, "90d": 90}


def _get_symbol_or_404(db: Session, ticker: str):
    symbol = sym_repo.get_by_ticker(db, ticker)
    if symbol is None:
        raise NotFoundError(
            "SYMBOL_NOT_FOUND", f"'{ticker.upper()}' sembolü bulunamadı veya izleme listenizde değil."
        )
    return symbol


@router.get("/search", response_model=SymbolSearchResponse)
def search_symbols(
    q: str = Query(min_length=1, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SymbolSearchResponse:
    results = sym_repo.search(db, q)
    in_watchlist = {s.id for _, s in wl_repo.list_for_user(db, current_user.id)}
    return SymbolSearchResponse(
        results=[
            SymbolSearchItem(
                symbol=s.ticker,
                company_name=s.company_name,
                already_in_watchlist=s.id in in_watchlist,
            )
            for s in results
        ]
    )


@router.get("/{ticker}/gex-profile", response_model=GexProfileResponse)
def get_gex_profile(
    ticker: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> GexProfileResponse:
    symbol = _get_symbol_or_404(db, ticker)
    summary = gex_repo.get_latest_summary(db, symbol.id)
    if summary is None:
        raise BusinessRuleError("NO_OPTIONS_DATA", "Bu sembol için opsiyon verisi bulunmuyor.")

    strikes = gex_repo.get_strikes_for_run(db, symbol.id, summary.calculation_run_id)

    # Aynı strike'ta birden fazla vade olabilir → grafik için strike bazında topla
    merged: dict[float, dict[str, float]] = {}
    for r in strikes:
        k = float(r.strike)
        acc = merged.setdefault(k, {"net": 0.0, "call": 0.0, "put": 0.0})
        acc["net"] += float(r.net_gex)
        acc["call"] += float(r.call_gex)
        acc["put"] += float(r.put_gex)

    return GexProfileResponse(
        symbol=symbol.ticker,
        spot_price=float(summary.spot_price_at_calc),
        gamma_flip_strike=float(summary.gamma_flip_strike) if summary.gamma_flip_strike is not None else None,
        call_wall_strike=float(summary.call_wall_strike) if summary.call_wall_strike is not None else None,
        put_wall_strike=float(summary.put_wall_strike) if summary.put_wall_strike is not None else None,
        regime=summary.regime,
        computed_at=summary.computed_at,
        strikes=[
            GexStrikePoint(strike=k, net_gex=v["net"], call_gex=v["call"], put_gex=v["put"])
            for k, v in sorted(merged.items())
        ],
    )


@router.get("/{ticker}/time-series", response_model=TimeSeriesResponse)
def get_time_series(
    ticker: str,
    range: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TimeSeriesResponse:
    symbol = _get_symbol_or_404(db, ticker)
    history = gex_repo.get_summary_history(db, symbol.id, RANGE_DAYS[range])
    return TimeSeriesResponse(
        symbol=symbol.ticker,
        series=[
            TimeSeriesPoint(
                date=h.computed_at,
                total_net_gex=float(h.total_net_gex),
                spot_price=float(h.spot_price_at_calc),
            )
            for h in history
        ],
    )


@router.get("/{ticker}/raw-data", response_model=RawDataResponse)
def get_raw_data(
    ticker: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RawDataResponse:
    symbol = _get_symbol_or_404(db, ticker)
    rows, total = gex_repo.get_raw_chain_page(db, symbol.id, page, page_size)
    return RawDataResponse(
        symbol=symbol.ticker,
        page=page,
        page_size=page_size,
        total_rows=total,
        rows=[
            RawDataRow(
                strike=float(r.strike),
                expiry=r.expiry,
                call_oi=r.call_oi,
                put_oi=r.put_oi,
                call_gamma=float(r.call_gamma) if r.call_gamma is not None else None,
                put_gamma=float(r.put_gamma) if r.put_gamma is not None else None,
            )
            for r in rows
        ],
    )
