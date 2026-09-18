"""Ana Panel endpoint'i — Build Spec Bölüm 7.3.

Bölüm 6.3: basit okuma senaryolarında router doğrudan repository çağırabilir;
servis katmanı yalnızca iş mantığı/hesaplama içeren akışlarda zorunludur.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.repositories import gex_repository as gex_repo
from app.repositories import watchlist_repository as wl_repo
from app.schemas.gex import (
    AttentionItem,
    DashboardResponse,
    SummaryStripItem,
    WatchlistPreviewItem,
)

router = APIRouter(tags=["Ana Panel"])

STALE_AFTER_MINUTES = 60
FLIP_PROXIMITY_PCT = 1.0  # spot, flip'e %1'den yakınsa dikkat gerektirir


def _age_minutes(ts: datetime) -> int:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - ts).total_seconds() // 60))


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    pairs = wl_repo.list_for_user(db, current_user.id)
    symbol_ids = [s.id for _, s in pairs]

    summaries = gex_repo.get_latest_summaries(db, symbol_ids)
    prices = gex_repo.get_latest_prices(db, symbol_ids)

    strip: list[SummaryStripItem] = []
    attention: list[AttentionItem] = []
    preview: list[WatchlistPreviewItem] = []
    last_updated: datetime | None = None

    for _, symbol in pairs:
        summary = summaries.get(symbol.id)
        price = prices.get(symbol.id)
        if summary is None:
            continue

        spot = float(summary.spot_price_at_calc)
        age = _age_minutes(summary.computed_at)
        if last_updated is None or summary.computed_at > last_updated:
            last_updated = summary.computed_at

        strip.append(
            SummaryStripItem(
                symbol=symbol.ticker,
                company_name=symbol.company_name,
                spot_price=spot,
                daily_change_pct=float(price.daily_change_pct) if price and price.daily_change_pct is not None else None,
                regime=summary.regime,
                data_age_minutes=age,
                is_stale=age > STALE_AFTER_MINUTES,
            )
        )

        preview.append(
            WatchlistPreviewItem(
                symbol=symbol.ticker,
                spot_price=spot,
                total_net_gex=float(summary.total_net_gex),
                sparkline=gex_repo.get_sparkline(db, symbol.id),
            )
        )

        # Dikkat gerektirenler: flip'e yakınlık
        if summary.gamma_flip_strike is not None and spot > 0:
            flip = float(summary.gamma_flip_strike)
            dist_pct = abs(spot - flip) / spot * 100
            if dist_pct <= FLIP_PROXIMITY_PCT:
                attention.append(
                    AttentionItem(
                        symbol=symbol.ticker,
                        type="flip_proximity",
                        message=f"Flip noktasına {abs(spot - flip):.2f}$ kaldı",
                    )
                )

        if summary.regime == "unknown":
            attention.append(
                AttentionItem(
                    symbol=symbol.ticker,
                    type="no_flip",
                    message="Belirgin bir gamma flip noktası tespit edilemedi",
                )
            )

    return DashboardResponse(
        last_updated=last_updated,
        summary_strip=strip,
        attention_items=attention,
        watchlist_preview=preview,
    )
