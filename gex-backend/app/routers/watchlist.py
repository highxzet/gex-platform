"""İzleme listesi endpoint'leri — Build Spec Bölüm 7.5."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.database import get_db
from app.models import User
from app.repositories import gex_repository as gex_repo
from app.repositories import symbol_repository as sym_repo
from app.repositories import watchlist_repository as wl_repo
from app.schemas.watchlist import (
    AddWatchlistRequest,
    ReorderRequest,
    WatchlistItemOut,
    WatchlistResponse,
)

router = APIRouter(prefix="/watchlist", tags=["İzleme Listesi"])


@router.get("", response_model=WatchlistResponse)
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchlistResponse:
    pairs = wl_repo.list_for_user(db, current_user.id)
    symbol_ids = [s.id for _, s in pairs]
    summaries = gex_repo.get_latest_summaries(db, symbol_ids)
    prices = gex_repo.get_latest_prices(db, symbol_ids)

    items: list[WatchlistItemOut] = []
    for _, symbol in pairs:
        summary = summaries.get(symbol.id)
        price = prices.get(symbol.id)
        spot = float(summary.spot_price_at_calc) if summary else (float(price.spot_price) if price else None)
        flip = float(summary.gamma_flip_strike) if summary and summary.gamma_flip_strike is not None else None

        items.append(
            WatchlistItemOut(
                symbol=symbol.ticker,
                company_name=symbol.company_name,
                spot_price=spot,
                daily_change_pct=float(price.daily_change_pct) if price and price.daily_change_pct is not None else None,
                total_net_gex=float(summary.total_net_gex) if summary else None,
                gamma_flip_strike=flip,
                flip_distance=(spot - flip) if (spot is not None and flip is not None) else None,
                regime=summary.regime if summary else None,
                sparkline=gex_repo.get_sparkline(db, symbol.id),
            )
        )
    return WatchlistResponse(items=items)


@router.post("", response_model=WatchlistItemOut, status_code=201)
def add_to_watchlist(
    payload: AddWatchlistRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WatchlistItemOut:
    symbol = sym_repo.get_by_ticker(db, payload.symbol)
    if symbol is None:
        raise NotFoundError(
            "SYMBOL_NOT_FOUND", f"'{payload.symbol.upper()}' sembolü bulunamadı veya izleme listenizde değil."
        )
    if wl_repo.exists(db, current_user.id, symbol.id):
        raise ConflictError("ALREADY_IN_WATCHLIST", "Bu sembol zaten izleme listenizde.")

    wl_repo.add(db, current_user.id, symbol.id)
    summary = gex_repo.get_latest_summary(db, symbol.id)
    return WatchlistItemOut(
        symbol=symbol.ticker,
        company_name=symbol.company_name,
        spot_price=float(summary.spot_price_at_calc) if summary else None,
        total_net_gex=float(summary.total_net_gex) if summary else None,
        regime=summary.regime if summary else None,
    )


@router.delete("/{ticker}", status_code=204, response_class=Response)
def remove_from_watchlist(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    symbol = sym_repo.get_by_ticker(db, ticker)
    if symbol is None:
        raise NotFoundError(
            "SYMBOL_NOT_FOUND", f"'{ticker.upper()}' sembolü bulunamadı veya izleme listenizde değil."
        )
    removed = wl_repo.remove(db, current_user.id, symbol.id)
    if removed == 0:
        raise NotFoundError("SYMBOL_NOT_FOUND", "Bu sembol izleme listenizde değil.")
    return Response(status_code=204)


@router.patch("/reorder", status_code=204, response_class=Response)
def reorder_watchlist(
    payload: ReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ids = []
    for ticker in payload.ordered_symbols:
        symbol = sym_repo.get_by_ticker(db, ticker)
        if symbol is not None:
            ids.append(symbol.id)
    wl_repo.reorder(db, current_user.id, ids)
    return Response(status_code=204)
