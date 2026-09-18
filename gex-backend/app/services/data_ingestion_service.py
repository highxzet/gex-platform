"""Veri alma servisi — Build Spec Bölüm 4 + 9.2.

Sorumluluk: sağlayıcıdan ham veriyi çekmek, normalize etmek ve `option_chain_raw`
/ `price_snapshots` tablolarına yazmak. Hesaplama YAPMAZ (o Calculation Engine'in işi).
"""
from __future__ import annotations

import logging
import time
from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.core.retry import fetch_with_retry
from app.models import OptionChainRaw, PriceSnapshot, Symbol
from app.providers.base import MarketDataProvider, OptionChainRow, PriceQuote

logger = logging.getLogger(__name__)


def fetch_symbol_data(
    provider: MarketDataProvider, ticker: str
) -> tuple[PriceQuote, list[OptionChainRow]]:
    """Bir sembolün fiyatını ve opsiyon zincirini retry ile çeker (Bölüm 4.5)."""
    price = fetch_with_retry(lambda: provider.get_price(ticker), label=f"{ticker} fiyat")
    chain = fetch_with_retry(
        lambda: provider.get_option_chain(ticker), label=f"{ticker} opsiyon zinciri"
    )
    return price, chain


def persist_raw_data(
    db: Session,
    symbol: Symbol,
    price: PriceQuote,
    chain: list[OptionChainRow],
    provider_name: str,
) -> None:
    """Ham veriyi denetim/yeniden hesaplama için saklar (Bölüm 5.3 / 5.4)."""
    db.add(
        PriceSnapshot(
            symbol_id=symbol.id,
            spot_price=price.spot_price,
            daily_change_pct=price.daily_change_pct,
            provider=provider_name,
        )
    )
    db.add_all(
        OptionChainRaw(
            symbol_id=symbol.id,
            strike=row.strike,
            expiry=row.expiry,
            call_oi=row.call_oi,
            put_oi=row.put_oi,
            call_gamma=row.call_gamma,
            put_gamma=row.put_gamma,
            call_iv=row.call_iv,
            put_iv=row.put_iv,
            provider=provider_name,
        )
        for row in chain
    )


def to_calculation_rows(chain: list[OptionChainRow], today: date | None = None) -> list[dict]:
    """Sağlayıcı satırlarını Calculation Engine'in beklediği sözlüklere çevirir.

    `expiry_years` burada hesaplanır (Bölüm 8.1 notu): motor tarih bilmez, saf kalır.
    """
    ref = today or date.today()
    rows: list[dict] = []
    for r in chain:
        days = (r.expiry - ref).days
        if days < 0:
            continue  # vadesi geçmiş kontrat (Bölüm 3.3 kenar durumu)
        rows.append(
            {
                "strike": r.strike,
                "expiry": r.expiry,
                "call_oi": r.call_oi,
                "put_oi": r.put_oi,
                "call_gamma": r.call_gamma,
                "put_gamma": r.put_gamma,
                "call_iv": r.call_iv,
                "put_iv": r.put_iv,
                "expiry_years": days / 365.0,
            }
        )
    return rows


def throttle() -> None:
    """Rate limit koruması — istekler arasına bilinçli gecikme (Bölüm 4.6)."""
    if settings.request_delay_seconds > 0:
        time.sleep(settings.request_delay_seconds)
