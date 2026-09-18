"""Calculation Engine birim testleri — Build Spec Bölüm 13.3.

Bölüm 3.11'deki elle hesaplanmış uçtan uca örnek birebir doğrulanır.
Bu modül %100 kapsam hedefindedir (Bölüm 13.7) — hesaplama hatası toleransı yoktur.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.services.calculation_engine import CalculationEngine

EXPIRY = date(2026, 10, 17)


# ---------- Bölüm 3.4 / 3.11: strike bazında GEX ----------
def test_strike_gex_calculation_matches_manual_example(calculation_engine):
    """Bölüm 3.11, Strike 95: call 200.000, put -360.000, net -160.000."""
    call_gex, put_gex, net_gex = calculation_engine.calculate_strike_gex(
        gamma_call=0.04, oi_call=500, gamma_put=0.03, oi_put=1200, spot=100.00
    )
    assert call_gex == pytest.approx(200_000, rel=1e-9)
    assert put_gex == pytest.approx(-360_000, rel=1e-9)
    assert net_gex == pytest.approx(-160_000, rel=1e-9)


def test_strike_gex_strike_100_and_105(calculation_engine):
    """Bölüm 3.11'in kalan iki strike'ı."""
    _, _, net_100 = calculation_engine.calculate_strike_gex(0.06, 2000, 0.06, 1800, 100.00)
    assert net_100 == pytest.approx(120_000, rel=1e-9)

    _, _, net_105 = calculation_engine.calculate_strike_gex(0.03, 1500, 0.02, 400, 100.00)
    assert net_105 == pytest.approx(370_000, rel=1e-9)


def test_strike_gex_respects_configurable_move_pct():
    """GEX_MOVE_PCT konfigüre edilebilir olmalı (Bölüm 3.4 / 15)."""
    engine = CalculationEngine(
        risk_free_rate=0.05, contract_multiplier=100, gex_move_pct=0.02, neutral_band_pct=0.002
    )
    call_gex, _, _ = engine.calculate_strike_gex(0.04, 500, 0.0, 0, 100.00)
    assert call_gex == pytest.approx(400_000, rel=1e-9)  # %1 yerine %2 -> iki katı


# ---------- Bölüm 3.7: gamma flip ----------
def test_gamma_flip_interpolation(calculation_engine):
    """Bölüm 3.11: kümülatif -160k / -40k / +330k -> flip = 100.5405.

    NOT (spec sapması): Build Spec Bölüm 3.11 bu örnek için 100.49 yazar, çünkü
    interpolasyonda strike 105'in KENDİ net GEX'ini (370.000) kullanır. Oysa
    Bölüm 3.7 algoritması açıkça KÜMÜLATİF değerlerle çalışır ve strike 105'teki
    kümülatif 330.000'dir (-40.000 + 370.000). Kümülatif eğrinin sıfırı kestiği
    nokta: 100 + 40.000/(40.000+330.000) * 5 = 100.5405.
    Algoritma otorite kabul edildi (Bölüm 21.5).
    """
    flip = calculation_engine.find_gamma_flip([95, 100, 105], [-160_000, -40_000, 330_000])
    assert flip == pytest.approx(100.5405, abs=0.001)


def test_gamma_flip_returns_none_when_no_sign_change(calculation_engine):
    flip = calculation_engine.find_gamma_flip([95, 100, 105], [100_000, 250_000, 400_000])
    assert flip is None


def test_gamma_flip_positive_to_negative(calculation_engine):
    """Ters yön: pozitiften negatife geçiş de yakalanmalı."""
    flip = calculation_engine.find_gamma_flip([95, 100], [100_000, -100_000])
    assert flip == pytest.approx(97.5, abs=0.01)


def test_gamma_flip_exact_zero_returns_that_strike(calculation_engine):
    """Kümülatif tam sıfırsa o strike doğrudan flip noktasıdır."""
    flip = calculation_engine.find_gamma_flip([95, 100, 105], [0.0, 50_000, 90_000])
    assert flip == 95


def test_gamma_flip_empty_input(calculation_engine):
    assert calculation_engine.find_gamma_flip([], []) is None


# ---------- Bölüm 3.8: call / put wall ----------
def test_call_and_put_wall_detection(calculation_engine):
    call_wall, put_wall = calculation_engine.find_walls({95: -160_000, 100: 120_000, 105: 370_000})
    assert call_wall == 105
    assert put_wall == 95


def test_walls_none_when_all_positive(calculation_engine):
    call_wall, put_wall = calculation_engine.find_walls({100: 10.0, 105: 20.0})
    assert call_wall == 105
    assert put_wall is None


def test_walls_none_when_all_negative(calculation_engine):
    call_wall, put_wall = calculation_engine.find_walls({100: -10.0, 105: -20.0})
    assert call_wall is None
    assert put_wall == 105  # en negatif


def test_walls_empty_map(calculation_engine):
    assert calculation_engine.find_walls({}) == (None, None)


# ---------- Bölüm 3.9: rejim ----------
def test_regime_positive(calculation_engine):
    assert calculation_engine.determine_regime(spot=110, gamma_flip=100) == "positive"


def test_regime_negative(calculation_engine):
    assert calculation_engine.determine_regime(spot=90, gamma_flip=100) == "negative"


def test_regime_neutral_within_band(calculation_engine):
    # spot 100.1, flip 100 -> fark %0.0999, bant %0.2 -> nötr
    assert calculation_engine.determine_regime(spot=100.1, gamma_flip=100) == "neutral"


def test_regime_unknown_when_no_flip(calculation_engine):
    assert calculation_engine.determine_regime(spot=100, gamma_flip=None) == "unknown"


# ---------- Bölüm 3.3: Black-Scholes gamma ----------
def test_black_scholes_gamma_zero_when_expired(calculation_engine):
    assert calculation_engine.black_scholes_gamma(S=100, K=100, T=0, sigma=0.25) == 0.0


def test_black_scholes_gamma_zero_when_invalid_iv(calculation_engine):
    assert calculation_engine.black_scholes_gamma(S=100, K=100, T=0.5, sigma=-0.1) == 0.0


def test_black_scholes_gamma_zero_when_invalid_price(calculation_engine):
    assert calculation_engine.black_scholes_gamma(S=0, K=100, T=0.5, sigma=0.25) == 0.0
    assert calculation_engine.black_scholes_gamma(S=100, K=0, T=0.5, sigma=0.25) == 0.0


def test_black_scholes_gamma_zero_when_none_inputs(calculation_engine):
    assert calculation_engine.black_scholes_gamma(S=100, K=100, T=0.5, sigma=None) == 0.0


def test_black_scholes_gamma_known_value(calculation_engine):
    """ATM, T=0.5, sigma=0.25, r=0.05 -> gamma = 0.0219795.

    d1 = 0.2298100, phi(d1) = 0.3885460, Gamma = 0.3885460 / 17.6776695 = 0.0219795
    """
    gamma = calculation_engine.black_scholes_gamma(S=100, K=100, T=0.5, sigma=0.25)
    assert gamma == pytest.approx(0.0219795, abs=1e-6)


def test_black_scholes_gamma_positive_otm(calculation_engine):
    """Gamma yönsüzdür ve pozitiftir (Bölüm 3.3)."""
    assert calculation_engine.black_scholes_gamma(S=100, K=105, T=0.3, sigma=0.3) > 0


# ---------- Bölüm 3.2: gamma kaynağı ----------
def test_resolve_gamma_prefers_provider_value(calculation_engine):
    result = calculation_engine.resolve_gamma(provided_gamma=0.055, S=100, K=100, T=0.5, iv=0.25)
    assert result == 0.055  # birebir sağlayıcı değeri, hesaplanmamış


def test_resolve_gamma_falls_back_to_black_scholes(calculation_engine):
    result = calculation_engine.resolve_gamma(provided_gamma=None, S=100, K=100, T=0.5, iv=0.25)
    assert result is not None
    assert result == pytest.approx(0.0219795, abs=1e-6)


def test_resolve_gamma_none_when_no_iv(calculation_engine):
    assert calculation_engine.resolve_gamma(None, S=100, K=100, T=0.5, iv=None) is None


def test_resolve_gamma_none_when_iv_non_positive(calculation_engine):
    assert calculation_engine.resolve_gamma(None, S=100, K=100, T=0.5, iv=0) is None


# ---------- Bölüm 3.11: uçtan uca ----------
def _manual_example_rows() -> list[dict]:
    return [
        {"strike": 95, "expiry": EXPIRY, "call_oi": 500, "put_oi": 1200,
         "call_gamma": 0.04, "put_gamma": 0.03, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        {"strike": 100, "expiry": EXPIRY, "call_oi": 2000, "put_oi": 1800,
         "call_gamma": 0.06, "put_gamma": 0.06, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        {"strike": 105, "expiry": EXPIRY, "call_oi": 1500, "put_oi": 400,
         "call_gamma": 0.03, "put_gamma": 0.02, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
    ]


def test_full_symbol_calculation_matches_manual_example(calculation_engine):
    """Bölüm 3.11'in tamamı: toplam, flip, wall'lar ve rejim."""
    summary = calculation_engine.calculate_symbol_gex(
        "TEST", spot=100.00, option_rows=_manual_example_rows()
    )

    assert summary.symbol == "TEST"
    assert summary.spot_price == 100.00
    assert summary.total_net_gex == pytest.approx(330_000, rel=1e-9)
    assert summary.gamma_flip_strike == pytest.approx(100.5405, abs=0.001)
    assert summary.call_wall_strike == 105
    assert summary.put_wall_strike == 95
    assert summary.regime == "negative"  # spot 100 < flip 100.49
    assert len(summary.strike_results) == 3


def test_full_calculation_strike_results_detail(calculation_engine):
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.00, _manual_example_rows())
    by_strike = {r.strike: r for r in summary.strike_results}
    assert by_strike[95].net_gex == pytest.approx(-160_000, rel=1e-9)
    assert by_strike[100].net_gex == pytest.approx(120_000, rel=1e-9)
    assert by_strike[105].net_gex == pytest.approx(370_000, rel=1e-9)
    assert by_strike[95].expiry == EXPIRY


def test_rows_without_gamma_or_iv_are_skipped(calculation_engine):
    """Gamma da IV de yoksa satır hesaplama dışı bırakılır (Bölüm 4.4)."""
    rows = _manual_example_rows() + [
        {"strike": 110, "expiry": EXPIRY, "call_oi": 999, "put_oi": 999,
         "call_gamma": None, "put_gamma": None, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
    ]
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.00, rows)
    assert len(summary.strike_results) == 3  # 110 atlandı
    assert summary.total_net_gex == pytest.approx(330_000, rel=1e-9)


def test_same_strike_multiple_expiries_are_aggregated(calculation_engine):
    """Aynı strike'ta iki vade -> flip/wall için strike bazında toplanır (Bölüm 8.1)."""
    rows = [
        {"strike": 100, "expiry": EXPIRY, "call_oi": 1000, "put_oi": 0,
         "call_gamma": 0.05, "put_gamma": 0.0, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        {"strike": 100, "expiry": date(2026, 11, 21), "call_oi": 1000, "put_oi": 0,
         "call_gamma": 0.05, "put_gamma": 0.0, "call_iv": None, "put_iv": None, "expiry_years": 0.2},
    ]
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.00, rows)
    assert len(summary.strike_results) == 2  # iki ayrı satır korunur
    assert summary.call_wall_strike == 100  # ama tek strike'ta toplanır
    assert summary.total_net_gex == pytest.approx(2 * 0.05 * 1000 * 100 * 10_000 * 0.01, rel=1e-9)


def test_empty_option_rows(calculation_engine):
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.00, [])
    assert summary.total_net_gex == 0.0
    assert summary.gamma_flip_strike is None
    assert summary.call_wall_strike is None
    assert summary.put_wall_strike is None
    assert summary.regime == "unknown"


def test_engine_uses_settings_defaults_when_not_overridden():
    """Parametre verilmezse ortam değişkeni varsayılanları kullanılır (Bölüm 15)."""
    engine = CalculationEngine()
    assert engine.contract_multiplier == 100
    assert engine.gex_move_pct == pytest.approx(0.01)
    assert engine.neutral_band_pct == pytest.approx(0.002)
    assert engine.risk_free_rate == pytest.approx(0.05)
