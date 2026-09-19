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
from app.providers import get_provider
from app.services.calculation_engine import CalculationEngine
from app.services.level_backtest_service import (
    _round_number_baseline,
    _touches_and_holds,
    analyze_levels,
)
from app.schemas.gex import (
    GexProfileResponse,
    GexStrikePoint,
    CandleOut,
    LevelOut,
    LevelBacktestResponse,
    LevelStatOut,
    PriceLevelsResponse,
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


@router.get("/{ticker}/price-levels", response_model=PriceLevelsResponse)
def get_price_levels(
    ticker: str,
    days: int = Query(90, ge=5, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PriceLevelsResponse:
    """Fiyat mumları + GEX'ten türetilmiş destek/direnç seviyeleri.

    Seviyeler en güncel hesaplama çalıştırmasının strike bazlı GEX'inden üretilir
    (bkz. CalculationEngine.compute_levels).
    """
    symbol = _get_symbol_or_404(db, ticker)
    summary = gex_repo.get_latest_summary(db, symbol.id)
    if summary is None:
        raise BusinessRuleError("NO_OPTIONS_DATA", "Bu sembol için opsiyon verisi bulunmuyor.")

    strikes = gex_repo.get_strikes_for_run(db, symbol.id, summary.calculation_run_id)
    strike_map: dict[float, float] = {}
    for r in strikes:
        strike_map[float(r.strike)] = strike_map.get(float(r.strike), 0.0) + float(r.net_gex)

    spot = float(summary.spot_price_at_calc)
    flip = float(summary.gamma_flip_strike) if summary.gamma_flip_strike is not None else None
    levels = CalculationEngine().compute_levels(strike_map, spot, flip)

    candles = get_provider().get_price_history(symbol.ticker, days)

    return PriceLevelsResponse(
        symbol=symbol.ticker,
        spot_price=spot,
        computed_at=summary.computed_at,
        candles=[
            CandleOut(date=c.date, open=c.open, high=c.high, low=c.low, close=c.close, volume=c.volume)
            for c in candles
        ],
        levels=[
            LevelOut(price=lv.price, kind=lv.kind, label=lv.label, strength=lv.strength, net_gex=lv.net_gex)
            for lv in levels
        ],
    )


@router.get("/{ticker}/level-backtest", response_model=LevelBacktestResponse)
def get_level_backtest(
    ticker: str,
    days: int = Query(365, ge=60, le=1825),
    forward_days: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> LevelBacktestResponse:
    """GEX seviyelerinin tarihsel olarak 'tutup tutmadığını' iki kontrol grubuyla ölçer.

    DÜRÜSTLÜK: bugünkü seviyeler geçmişe uygulanır (GEX geçmişi yok), bu yüzden
    döngüsellik riski taşır. Kesin yargı EOD anlık görüntüleri biriktikten sonra.
    """
    symbol = _get_symbol_or_404(db, ticker)
    summary = gex_repo.get_latest_summary(db, symbol.id)
    if summary is None:
        raise BusinessRuleError("NO_OPTIONS_DATA", "Bu sembol için opsiyon verisi bulunmuyor.")

    strikes = gex_repo.get_strikes_for_run(db, symbol.id, summary.calculation_run_id)
    strike_map: dict[float, float] = {}
    for r in strikes:
        strike_map[float(r.strike)] = strike_map.get(float(r.strike), 0.0) + float(r.net_gex)

    spot = float(summary.spot_price_at_calc)
    flip = float(summary.gamma_flip_strike) if summary.gamma_flip_strike is not None else None
    levels = CalculationEngine().compute_levels(strike_map, spot, flip)

    candles = get_provider().get_price_history(symbol.ticker, days)
    result = analyze_levels(
        symbol.ticker,
        candles,
        [(lv.label, lv.kind, lv.price) for lv in levels],
        forward_days=forward_days,
    )

    # Yuvarlak sayı kontrolü (sert baseline): strike ızgarası adımını tahmin et
    ks = sorted(strike_map)
    step = min((b - a) for a, b in zip(ks, ks[1:])) if len(ks) > 1 else 5.0
    round_rate, _n = _round_number_baseline(candles, forward_days, step, seed=abs(hash(symbol.ticker)) & 0xFFFF)

    # GEX seviyelerinin dokunuş-ağırlıklı toplam tutma oranı
    tot_t = sum(s.touches for s in result.levels if s.hold_rate is not None)
    tot_h = sum(s.holds for s in result.levels if s.hold_rate is not None)
    gex_rate = (tot_h / tot_t) if tot_t else None

    return LevelBacktestResponse(
        symbol=symbol.ticker,
        days=result.days,
        forward_days=forward_days,
        levels=[
            LevelStatOut(
                label=s.label, kind=s.kind, price=s.price,
                touches=s.touches, holds=s.holds, hold_rate=s.hold_rate,
            )
            for s in result.levels
        ],
        baseline_random=result.baseline_hold_rate,
        baseline_round=round_rate,
        gex_hold_rate=gex_rate,
        verdict=result.verdict,
    )
