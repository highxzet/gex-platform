"""Veri kaynağı soyutlama katmanı — Build Spec Bölüm 4.3.

KRİTİK MİMARİ KARAR: Veri kaynağı asla doğrudan Calculation Engine veya API
katmanına bağlı olmamalı. Her sağlayıcı bu arayüzü uygular; sağlayıcı değişikliği
tek dosyalık bir iş olur.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class OptionChainRow:
    """Normalize edilmiş tek bir strike/expiry satırı (Bölüm 4.4)."""

    symbol: str
    strike: float
    expiry: date
    call_oi: int
    put_oi: int
    call_gamma: float | None  # None ise Calculation Engine Black-Scholes ile hesaplar (Yol B)
    put_gamma: float | None
    call_iv: float | None
    put_iv: float | None


@dataclass
class PriceQuote:
    """Anlık fiyat bilgisi.

    (Bölüm 4.3'te `PriceSnapshot` adıyla geçer; burada `PriceQuote` denmesinin
    tek sebebi aynı adlı SQLAlchemy modeliyle karışmamasıdır.)
    """

    symbol: str
    spot_price: float
    daily_change_pct: float
    timestamp: datetime


class MarketDataProvider(ABC):
    """Tüm veri sağlayıcılarının uyması gereken sözleşme."""

    @abstractmethod
    def get_option_chain(self, symbol: str) -> list[OptionChainRow]:
        """Sembolün tüm vadeleri için normalize edilmiş opsiyon zinciri."""

    @abstractmethod
    def get_price(self, symbol: str) -> PriceQuote:
        """Sembolün güncel spot fiyatı ve günlük değişimi."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Kayıtlarda saklanacak sağlayıcı adı (ör. 'yfinance')."""
