"""Veri sağlayıcı fabrikası — Build Spec Bölüm 4.2 / 15.

`MARKET_DATA_PROVIDER` ortam değişkeni hangi sağlayıcının kullanılacağını belirler.
Yeni sağlayıcı eklemek: sınıfı yaz, buraya kaydet — başka hiçbir yer değişmez.
"""
from __future__ import annotations

from app.config import settings
from app.providers.base import MarketDataProvider, OptionChainRow, PriceQuote
from app.providers.yfinance_provider import YFinanceProvider

__all__ = [
    "MarketDataProvider",
    "OptionChainRow",
    "PriceQuote",
    "YFinanceProvider",
    "get_provider",
]

_PROVIDERS: dict[str, type[MarketDataProvider]] = {
    "yfinance": YFinanceProvider,
    # "tradier": TradierProvider,   # API anahtarı gerektirir (Bölüm 4.2)
    # "polygon": PolygonProvider,
}


def get_provider(name: str | None = None) -> MarketDataProvider:
    key = (name or settings.market_data_provider).lower()
    provider_cls = _PROVIDERS.get(key)
    if provider_cls is None:
        raise ValueError(
            f"Bilinmeyen veri sağlayıcı: '{key}'. Geçerli seçenekler: {sorted(_PROVIDERS)}"
        )
    return provider_cls()
