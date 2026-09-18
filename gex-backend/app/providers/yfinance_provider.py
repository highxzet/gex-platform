"""yfinance sağlayıcısı — Build Spec Bölüm 4.3 / 4.4.

yfinance gamma DÖNDÜRMEZ; yalnızca OI ve implied volatility verir. Bu yüzden
gamma, Calculation Engine tarafından Black-Scholes ile hesaplanır (Bölüm 3.2 Yol B).

Resmi bir API değildir — kırılgan olabilir; üretimde Tradier/Polygon'a geçiş için
`MarketDataProvider` arayüzü korunur.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

import yfinance as yf

from app.providers.base import Candle, MarketDataProvider, OptionChainRow, PriceQuote

logger = logging.getLogger(__name__)


def _clean_float(value: object) -> float | None:
    """NaN/None/negatif-olmayan dönüşümü — normalizasyon kuralı (Bölüm 4.4)."""
    if value is None:
        return None
    try:
        f = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _clean_oi(value: object) -> int:
    """OI eksik/NaN ise 0 (0 OI = 0 GEX katkısı, matematiksel olarak tutarlı)."""
    f = _clean_float(value)
    if f is None or f < 0:
        return 0
    return int(f)


class YFinanceProvider(MarketDataProvider):
    def get_provider_name(self) -> str:
        return "yfinance"

    def get_price(self, symbol: str) -> PriceQuote:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        last = _clean_float(info.get("lastPrice"))
        prev = _clean_float(info.get("previousClose"))
        if last is None or last <= 0:
            raise ValueError(f"{symbol}: geçerli spot fiyat alınamadı")

        change_pct = 0.0
        if prev is not None and prev > 0:
            change_pct = (last - prev) / prev * 100

        return PriceQuote(
            symbol=symbol,
            spot_price=last,
            daily_change_pct=change_pct,
            timestamp=datetime.now(timezone.utc),
        )

    def get_price_history(self, symbol: str, days: int = 90) -> list[Candle]:
        """Günlük OHLC geçmişi. Boş/eksik satırlar atlanır (Bölüm 4.4)."""
        period = f"{max(days, 5)}d"
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False)
        if df is None or df.empty:
            logger.warning("%s: fiyat geçmişi boş döndü", symbol)
            return []

        candles: list[Candle] = []
        for idx, row in df.iterrows():
            o, h, l, c = (_clean_float(row.get(k)) for k in ("Open", "High", "Low", "Close"))
            if None in (o, h, l, c) or c <= 0:
                continue
            candles.append(
                Candle(
                    date=idx.date(),
                    open=round(o, 4),
                    high=round(h, 4),
                    low=round(l, 4),
                    close=round(c, 4),
                    volume=_clean_oi(row.get("Volume")),
                )
            )
        return candles

    def get_option_chain(self, symbol: str) -> list[OptionChainRow]:
        ticker = yf.Ticker(symbol)
        expiries = ticker.options or []
        if not expiries:
            logger.warning("%s: opsiyon vadesi bulunamadı", symbol)
            return []

        rows: list[OptionChainRow] = []
        for expiry_str in expiries:
            try:
                chain = ticker.option_chain(expiry_str)
            except Exception as e:  # noqa: BLE001 — tek vade hatası tümünü durdurmaz
                logger.warning("%s %s vadesi çekilemedi: %s", symbol, expiry_str, e)
                continue

            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            calls = chain.calls.set_index("strike") if not chain.calls.empty else None
            puts = chain.puts.set_index("strike") if not chain.puts.empty else None

            strikes: set[float] = set()
            if calls is not None:
                strikes |= set(calls.index)
            if puts is not None:
                strikes |= set(puts.index)

            for strike in strikes:
                call_row = calls.loc[strike] if calls is not None and strike in calls.index else None
                put_row = puts.loc[strike] if puts is not None and strike in puts.index else None

                rows.append(
                    OptionChainRow(
                        symbol=symbol,
                        # Normalizasyon: strike her zaman float, 2 ondalık (Bölüm 4.4)
                        strike=round(float(strike), 2),
                        expiry=expiry_date,
                        call_oi=_clean_oi(call_row["openInterest"]) if call_row is not None else 0,
                        put_oi=_clean_oi(put_row["openInterest"]) if put_row is not None else 0,
                        # yfinance gamma vermez → Yol B (Black-Scholes)
                        call_gamma=None,
                        put_gamma=None,
                        call_iv=_clean_float(call_row["impliedVolatility"]) if call_row is not None else None,
                        put_iv=_clean_float(put_row["impliedVolatility"]) if put_row is not None else None,
                    )
                )

        return rows
