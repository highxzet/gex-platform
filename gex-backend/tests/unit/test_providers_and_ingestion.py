"""Provider, veri alma, retry ve piyasa saati testleri.

Build Spec Bölüm 13.7: `providers/` için mock veri ile temel akış testi
(gerçek API'ye bağımlı testler CI'da çalıştırılmaz).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import pytest
import pytz

from app.core.market_hours import is_market_open
from app.core.retry import fetch_with_retry
from app.providers import get_provider
from app.providers.base import OptionChainRow
from app.providers.yfinance_provider import YFinanceProvider, _clean_float, _clean_oi
from app.services.data_ingestion_service import to_calculation_rows

ET = pytz.timezone("America/New_York")


# ---------- Normalizasyon (Bölüm 4.4) ----------
@pytest.mark.parametrize(
    "value,expected",
    [(None, None), ("abc", None), (float("nan"), None), (float("inf"), None), (3.5, 3.5), ("2.5", 2.5)],
)
def test_clean_float(value, expected):
    assert _clean_float(value) == expected


@pytest.mark.parametrize("value,expected", [(None, 0), (float("nan"), 0), (-5, 0), (12.9, 12), (7, 7)])
def test_clean_oi_missing_becomes_zero(value, expected):
    """OI eksik/geçersizse 0 (0 OI = 0 GEX katkısı, matematiksel olarak tutarlı)."""
    assert _clean_oi(value) == expected


# ---------- Provider fabrikası (Bölüm 4.2) ----------
def test_get_provider_returns_yfinance_by_default():
    assert get_provider().get_provider_name() == "yfinance"


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Bilinmeyen veri sağlayıcı"):
        get_provider("boyle-bir-saglayici-yok")


# ---------- YFinanceProvider (mock'lu) ----------
class _FakeChain:
    def __init__(self, calls: pd.DataFrame, puts: pd.DataFrame):
        self.calls = calls
        self.puts = puts


class _FakeTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.fast_info = {"lastPrice": 100.0, "previousClose": 98.0}
        self.options = ("2026-12-18",)

    def option_chain(self, expiry: str):  # noqa: ARG002
        calls = pd.DataFrame(
            {"strike": [95.0, 100.0], "openInterest": [10, 20], "impliedVolatility": [0.25, 0.30]}
        )
        puts = pd.DataFrame(
            {"strike": [100.0, 105.0], "openInterest": [30, 40], "impliedVolatility": [0.28, 0.33]}
        )
        return _FakeChain(calls, puts)


def test_yfinance_get_price(monkeypatch):
    monkeypatch.setattr("app.providers.yfinance_provider.yf.Ticker", _FakeTicker)
    quote = YFinanceProvider().get_price("TST")
    assert quote.spot_price == 100.0
    assert quote.daily_change_pct == pytest.approx((100 - 98) / 98 * 100)


def test_yfinance_get_price_invalid_raises(monkeypatch):
    class _Bad(_FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.fast_info = {"lastPrice": None, "previousClose": 98.0}

    monkeypatch.setattr("app.providers.yfinance_provider.yf.Ticker", _Bad)
    with pytest.raises(ValueError, match="geçerli spot fiyat"):
        YFinanceProvider().get_price("TST")


def test_yfinance_option_chain_merges_calls_and_puts(monkeypatch):
    monkeypatch.setattr("app.providers.yfinance_provider.yf.Ticker", _FakeTicker)
    rows = YFinanceProvider().get_option_chain("TST")

    by_strike = {r.strike: r for r in rows}
    assert set(by_strike) == {95.0, 100.0, 105.0}
    # yalnız call tarafı olan strike -> put_oi 0
    assert by_strike[95.0].call_oi == 10 and by_strike[95.0].put_oi == 0
    # her iki taraf
    assert by_strike[100.0].call_oi == 20 and by_strike[100.0].put_oi == 30
    # yalnız put tarafı
    assert by_strike[105.0].call_oi == 0 and by_strike[105.0].put_oi == 40
    # yfinance gamma vermez -> Yol B (Black-Scholes)
    assert all(r.call_gamma is None and r.put_gamma is None for r in rows)
    assert by_strike[100.0].expiry == date(2026, 12, 18)


def test_yfinance_no_expiries_returns_empty(monkeypatch):
    class _NoOpts(_FakeTicker):
        def __init__(self, symbol):
            super().__init__(symbol)
            self.options = ()

    monkeypatch.setattr("app.providers.yfinance_provider.yf.Ticker", _NoOpts)
    assert YFinanceProvider().get_option_chain("TST") == []


def test_yfinance_expiry_error_is_skipped(monkeypatch):
    """Tek vadenin hatası tüm zinciri düşürmez (kısmi başarısızlık)."""

    class _Broken(_FakeTicker):
        def option_chain(self, expiry):
            raise RuntimeError("yahoo patladi")

    monkeypatch.setattr("app.providers.yfinance_provider.yf.Ticker", _Broken)
    assert YFinanceProvider().get_option_chain("TST") == []


# ---------- to_calculation_rows (Bölüm 8.1 notu) ----------
def _row(expiry: date) -> OptionChainRow:
    return OptionChainRow(
        symbol="TST", strike=100.0, expiry=expiry, call_oi=1, put_oi=1,
        call_gamma=None, put_gamma=None, call_iv=0.25, put_iv=0.25,
    )


def test_to_calculation_rows_computes_expiry_years():
    today = date(2026, 1, 1)
    rows = to_calculation_rows([_row(date(2026, 7, 2))], today)
    assert rows[0]["expiry_years"] == pytest.approx(182 / 365.0)


def test_to_calculation_rows_drops_expired():
    today = date(2026, 6, 1)
    assert to_calculation_rows([_row(date(2026, 5, 1))], today) == []


def test_to_calculation_rows_keeps_today_expiry():
    today = date(2026, 6, 1)
    rows = to_calculation_rows([_row(today)], today)
    assert len(rows) == 1
    assert rows[0]["expiry_years"] == 0.0


# ---------- Retry (Bölüm 4.5) ----------
def test_fetch_with_retry_succeeds_first_try():
    assert fetch_with_retry(lambda: "ok", max_retries=3, backoff_seconds=0) == "ok"


def test_fetch_with_retry_recovers_after_failure():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("gecici hata")
        return "sonunda"

    assert fetch_with_retry(flaky, max_retries=3, backoff_seconds=0) == "sonunda"
    assert calls["n"] == 3


def test_fetch_with_retry_raises_after_all_attempts():
    def always_fails():
        raise RuntimeError("kalici hata")

    with pytest.raises(RuntimeError, match="kalici hata"):
        fetch_with_retry(always_fails, max_retries=2, backoff_seconds=0)


# ---------- Piyasa saatleri (Bölüm 4.7) ----------
def test_market_closed_on_weekend():
    saturday = ET.localize(datetime(2026, 9, 19, 12, 0))  # cumartesi
    assert is_market_open(saturday) is False


def test_market_open_during_weekday_session():
    friday_noon = ET.localize(datetime(2026, 9, 18, 12, 0))
    assert is_market_open(friday_noon) is True


def test_market_closed_before_open_and_after_close():
    assert is_market_open(ET.localize(datetime(2026, 9, 18, 9, 0))) is False
    assert is_market_open(ET.localize(datetime(2026, 9, 18, 16, 30))) is False


def test_market_open_at_exact_boundaries():
    assert is_market_open(ET.localize(datetime(2026, 9, 18, 9, 30))) is True
    assert is_market_open(ET.localize(datetime(2026, 9, 18, 16, 0))) is True
