"""TradingView Pine Script dışa aktarımı — Build Spec kapsamı dışı ek özellik.

Pine dışarıdan veri çekemediği için seviyeler script'e gömülür (bkz.
`pine_export_service` modül açıklaması).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.database import get_db
from app.models import Symbol, User
from app.repositories import gex_repository as gex_repo
from app.repositories import symbol_repository as sym_repo
from app.repositories import watchlist_repository as wl_repo
from app.schemas.gex import PineScriptResponse
from app.services.calculation_engine import CalculationEngine
from app.services.pine_export_service import SymbolLevels, build_pine_script

router = APIRouter(prefix="/pine", tags=["Pine Script"])


def _levels_for(db: Session, symbol: Symbol, engine: CalculationEngine) -> SymbolLevels | None:
    """Bir sembolün en güncel GEX seviyelerini Pine formatına hazırlar."""
    summary = gex_repo.get_latest_summary(db, symbol.id)
    if summary is None:
        return None

    strikes = gex_repo.get_strikes_for_run(db, symbol.id, summary.calculation_run_id)
    if not strikes:
        return None

    strike_map: dict[float, float] = {}
    for r in strikes:
        strike_map[float(r.strike)] = strike_map.get(float(r.strike), 0.0) + float(r.net_gex)

    spot = float(summary.spot_price_at_calc)
    flip = float(summary.gamma_flip_strike) if summary.gamma_flip_strike is not None else None
    levels = engine.compute_levels(strike_map, spot, flip)

    call_wall = next((lv.price for lv in levels if lv.label == "Call Wall"), None)
    put_wall = next((lv.price for lv in levels if lv.label == "Put Wall"), None)
    # Wall dışındaki dirençler/destekler, spot'a yakınlık sırasıyla
    resistances = sorted(
        (lv.price for lv in levels if lv.kind == "resistance" and lv.label != "Call Wall")
    )
    supports = sorted(
        (lv.price for lv in levels if lv.kind == "support" and lv.label != "Put Wall"),
        reverse=True,
    )

    return SymbolLevels(
        ticker=symbol.ticker,
        spot=spot,
        call_wall=call_wall,
        put_wall=put_wall,
        flip=flip,
        resistances=resistances,
        supports=supports,
    )


@router.get("/watchlist", response_model=PineScriptResponse)
def pine_for_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PineScriptResponse:
    """İzleme listesindeki TÜM sembolleri kapsayan tek bir Pine indikatörü.

    TradingView'de sembolü değiştirdiğinizde script otomatik olarak o sembolün
    seviyelerini çizer.
    """
    engine = CalculationEngine()
    pairs = wl_repo.list_for_user(db, current_user.id)

    collected: list[SymbolLevels] = []
    skipped: list[str] = []
    for _, symbol in pairs:
        lv = _levels_for(db, symbol, engine)
        if lv is None:
            skipped.append(symbol.ticker)
        else:
            collected.append(lv)

    if not collected:
        raise BusinessRuleError(
            "NO_OPTIONS_DATA",
            "İzleme listenizdeki hiçbir sembol için hesaplanmış GEX verisi yok.",
        )

    script = build_pine_script(collected, title="GEX Seviyeleri — İzleme Listesi")
    return PineScriptResponse(
        script=script,
        symbols=[lv.ticker for lv in collected],
        skipped=skipped,
        line_count=script.count("\n") + 1,
    )


@router.get("/symbol/{ticker}", response_model=PineScriptResponse)
def pine_for_symbol(
    ticker: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PineScriptResponse:
    """Tek sembol için Pine indikatörü."""
    symbol = sym_repo.get_by_ticker(db, ticker)
    if symbol is None:
        raise NotFoundError(
            "SYMBOL_NOT_FOUND", f"'{ticker.upper()}' sembolü bulunamadı veya izleme listenizde değil."
        )

    lv = _levels_for(db, symbol, CalculationEngine())
    if lv is None:
        raise BusinessRuleError("NO_OPTIONS_DATA", "Bu sembol için opsiyon verisi bulunmuyor.")

    script = build_pine_script([lv], title=f"GEX Seviyeleri — {symbol.ticker}")
    return PineScriptResponse(
        script=script, symbols=[symbol.ticker], skipped=[], line_count=script.count("\n") + 1
    )


@router.get("/symbol/{ticker}/raw", response_class=PlainTextResponse)
def pine_raw(
    ticker: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> str:
    """Ham Pine kaynağı (indirme/kopyalama kolaylığı için düz metin)."""
    return pine_for_symbol(ticker, db, _).script  # type: ignore[arg-type]


@router.get("/watchlist/raw", response_class=PlainTextResponse)
def pine_watchlist_raw(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    return pine_for_watchlist(db, current_user).script
