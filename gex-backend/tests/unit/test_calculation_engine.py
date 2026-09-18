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


def test_full_symbol_calculation_matches_manual_example(calculation_engine, monkeypatch):
    """Bölüm 3.11'in tamamı: toplam, flip, wall'lar ve rejim.

    Bölüm 3.11 kümülatif-strike yöntemini varsayar; bu test onu doğruladığı için
    yöntemi açıkça seçer (varsayılan üretim yöntemi zero_gamma'dır).
    """
    from app.services import calculation_engine as ce

    monkeypatch.setattr(ce.settings, "gamma_flip_method", "cumulative_strike")
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


# ---------- Gamma flip seçimi (gerçek veri gürültüsüne dayanıklılık) ----------
def test_find_all_gamma_flips_returns_every_crossing(calculation_engine):
    """Kümülatif birden fazla kez sıfırı kesebilir; hepsi bulunmalı."""
    strikes = [100, 110, 120, 130]
    cumulative = [-10.0, 10.0, -10.0, 10.0]
    flips = calculation_engine.find_all_gamma_flips(strikes, cumulative)
    assert len(flips) == 3
    assert flips == pytest.approx([105.0, 115.0, 125.0])


def test_find_all_gamma_flips_empty_when_no_crossing(calculation_engine):
    assert calculation_engine.find_all_gamma_flips([100, 110], [5.0, 10.0]) == []


def test_select_gamma_flip_picks_nearest_to_spot(calculation_engine):
    """Derin OTM gürültüsü (105) değil, spot'a yakın gerçek geçiş (125) seçilmeli."""
    strikes = [100, 110, 120, 130]
    cumulative = [-10.0, 10.0, -10.0, 10.0]  # kesişimler: 105, 115, 125
    assert calculation_engine.select_gamma_flip(strikes, cumulative, spot=124.0) == pytest.approx(125.0)


def test_select_gamma_flip_none_when_no_crossing(calculation_engine):
    assert calculation_engine.select_gamma_flip([100, 110], [5.0, 10.0], spot=105) is None


def test_select_gamma_flip_first_mode_matches_spec(calculation_engine, monkeypatch):
    """GAMMA_FLIP_SELECTION='first' -> Bölüm 3.7'nin birebir davranışı."""
    from app.services import calculation_engine as ce_module

    monkeypatch.setattr(ce_module.settings, "gamma_flip_selection", "first")
    strikes = [100, 110, 120, 130]
    cumulative = [-10.0, 10.0, -10.0, 10.0]
    # spot 124'e rağmen İLK kesişim (105) dönmeli
    assert calculation_engine.select_gamma_flip(strikes, cumulative, spot=124.0) == pytest.approx(105.0)


def test_calculate_symbol_gex_uses_nearest_spot_flip(calculation_engine, monkeypatch):
    """Uçtan uca (kümülatif yöntem): gürültülü düşük strike'lar flip'i kaçırtmamalı."""
    from app.services import calculation_engine as ce

    monkeypatch.setattr(ce.settings, "gamma_flip_method", "cumulative_strike")
    rows = [
        # gürültü bölgesi: çok küçük gamma/OI
        {"strike": 50, "expiry": EXPIRY, "call_oi": 1, "put_oi": 2,
         "call_gamma": 0.001, "put_gamma": 0.001, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        {"strike": 60, "expiry": EXPIRY, "call_oi": 3, "put_oi": 1,
         "call_gamma": 0.001, "put_gamma": 0.001, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        # gerçek aksiyon: spot çevresi
        {"strike": 100, "expiry": EXPIRY, "call_oi": 100, "put_oi": 5000,
         "call_gamma": 0.05, "put_gamma": 0.05, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
        {"strike": 110, "expiry": EXPIRY, "call_oi": 8000, "put_oi": 100,
         "call_gamma": 0.05, "put_gamma": 0.05, "call_iv": None, "put_iv": None, "expiry_years": 0.1},
    ]
    summary = calculation_engine.calculate_symbol_gex("TEST", spot=105.0, option_rows=rows)
    assert summary.gamma_flip_strike is not None
    # 50-60 bölgesindeki gürültü değil, 100-110 arasındaki gerçek geçiş seçilmeli
    assert 100 <= summary.gamma_flip_strike <= 110


def test_find_all_gamma_flips_exact_zero_is_a_crossing(calculation_engine):
    """Kümülatif tam sıfırsa o strike doğrudan kesişim sayılır."""
    flips = calculation_engine.find_all_gamma_flips([95, 100, 105], [0.0, 50.0, 90.0])
    assert flips == [95]


# ---------- Zero-gamma level (endüstri standardı flip) ----------
def _iv_rows(strikes_oi: list[tuple[float, int, int]]) -> list[dict]:
    """IV'li satırlar üretir (gamma Black-Scholes ile S'e göre yeniden hesaplanır)."""
    return [
        {"strike": k, "expiry": EXPIRY, "call_oi": c, "put_oi": p,
         "call_gamma": None, "put_gamma": None, "call_iv": 0.25, "put_iv": 0.25,
         "expiry_years": 0.25}
        for k, c, p in strikes_oi
    ]


def test_total_net_gex_at_recomputes_gamma_with_spot(calculation_engine):
    """Aynı satırlar, farklı hipotetik spot -> farklı toplam GEX."""
    # NOT: gamma call ve put için AYNIdır; simetrik OI net GEX'i tam sıfır yapar.
    # Bu yüzden asimetrik OI kullanılıyor.
    rows = _iv_rows([(90, 100, 400), (100, 2000, 500), (110, 400, 100)])
    a = calculation_engine.total_net_gex_at(rows, 100.0)
    b = calculation_engine.total_net_gex_at(rows, 130.0)
    assert a != b
    assert a != 0.0


def test_total_net_gex_at_zero_spot_is_zero(calculation_engine):
    assert calculation_engine.total_net_gex_at(_iv_rows([(100, 1, 1)]), 0.0) == 0.0


def test_total_net_gex_at_uses_provider_gamma_when_given(calculation_engine):
    """Sağlayıcı gamma'sı sabittir; S ile yeniden hesaplanmaz (yalnız S^2 faktörü değişir)."""
    rows = [{"strike": 100, "expiry": EXPIRY, "call_oi": 1000, "put_oi": 0,
             "call_gamma": 0.05, "put_gamma": 0.0, "call_iv": None, "put_iv": None,
             "expiry_years": 0.25}]
    total = calculation_engine.total_net_gex_at(rows, 100.0)
    assert total == pytest.approx(0.05 * 1000 * 100 * 100**2 * 0.01, rel=1e-9)


def test_zero_gamma_level_found_near_spot(calculation_engine):
    """Put ağırlığı altta, call ağırlığı üstte -> sıfır geçişi arada olmalı."""
    rows = _iv_rows([(90, 100, 4000), (100, 2000, 2000), (110, 4000, 100)])
    z = calculation_engine.compute_zero_gamma_level(rows, spot=100.0)
    assert z is not None
    assert 85 <= z <= 115


def test_zero_gamma_level_none_when_no_crossing(calculation_engine):
    """Sadece call OI -> GEX her fiyatta pozitif, kesişim yok."""
    rows = _iv_rows([(90, 1000, 0), (100, 1000, 0), (110, 1000, 0)])
    assert calculation_engine.compute_zero_gamma_level(rows, spot=100.0) is None


def test_zero_gamma_level_empty_rows(calculation_engine):
    assert calculation_engine.compute_zero_gamma_level([], spot=100.0) is None
    assert calculation_engine.compute_zero_gamma_level(_iv_rows([(100, 1, 1)]), spot=0) is None


def test_calculate_symbol_gex_uses_zero_gamma_by_default(calculation_engine):
    rows = _iv_rows([(90, 100, 4000), (100, 2000, 2000), (110, 4000, 100)])
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.0, rows)
    assert summary.gamma_flip_strike is not None
    assert 85 <= summary.gamma_flip_strike <= 115


def test_cumulative_strike_method_still_available(calculation_engine, monkeypatch):
    """GAMMA_FLIP_METHOD='cumulative_strike' -> Bölüm 3.7 yöntemi."""
    from app.services import calculation_engine as ce

    monkeypatch.setattr(ce.settings, "gamma_flip_method", "cumulative_strike")
    summary = calculation_engine.calculate_symbol_gex("TEST", 100.00, _manual_example_rows())
    assert summary.gamma_flip_strike == pytest.approx(100.5405, abs=0.001)


def test_zero_gamma_level_handles_flat_zero_curve(calculation_engine):
    """Tüm OI sıfırsa GEX eğrisi her fiyatta 0'dır; bu da bir kesişim sayılır."""
    rows = _iv_rows([(90, 0, 0), (100, 0, 0), (110, 0, 0)])
    z = calculation_engine.compute_zero_gamma_level(rows, spot=100.0)
    assert z is not None
    # Düz sıfır eğride her grid noktası kesişim sayılır; spot'a en yakını seçilir.
    assert z == pytest.approx(100.0, abs=1.0)


# ---------- Destek / Direnç seviyeleri ----------
def _level_map() -> dict[float, float]:
    """Spot 100 varsayımıyla: üstte pozitif (direnç), altta negatif (destek)."""
    return {90.0: -8e6, 95.0: -5e6, 98.0: -1e6, 103.0: 2e6, 105.0: 20e6, 110.0: 9e6}


def test_compute_levels_classifies_support_and_resistance(calculation_engine):
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0)
    res = [lv for lv in levels if lv.kind == "resistance"]
    sup = [lv for lv in levels if lv.kind == "support"]
    assert all(lv.price > 100 for lv in res)
    assert all(lv.price < 100 for lv in sup)
    assert len(res) == 3 and len(sup) == 3


def test_compute_levels_first_ones_are_walls(calculation_engine):
    """En güçlü direnç 'Call Wall', en güçlü destek 'Put Wall' etiketlenir."""
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0)
    call_wall = next(lv for lv in levels if lv.label == "Call Wall")
    put_wall = next(lv for lv in levels if lv.label == "Put Wall")
    assert call_wall.price == 105.0  # en yüksek pozitif GEX
    assert put_wall.price == 90.0  # en negatif GEX


def test_compute_levels_strength_is_normalized(calculation_engine):
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0)
    strengths = [lv.strength for lv in levels if lv.kind != "flip"]
    assert max(strengths) == pytest.approx(1.0)  # en güçlü seviye 1.0
    assert all(0 <= s <= 1 for s in strengths)


def test_compute_levels_includes_gamma_flip(calculation_engine):
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0, gamma_flip=99.5)
    flip = next(lv for lv in levels if lv.kind == "flip")
    assert flip.price == 99.5
    assert flip.label == "Gamma Flip"


def test_compute_levels_sorted_by_price_desc(calculation_engine):
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0, gamma_flip=99.5)
    prices = [lv.price for lv in levels]
    assert prices == sorted(prices, reverse=True)


def test_compute_levels_respects_top_n(calculation_engine):
    levels = calculation_engine.compute_levels(_level_map(), spot=100.0, top_n=1)
    assert len([lv for lv in levels if lv.kind == "resistance"]) == 1
    assert len([lv for lv in levels if lv.kind == "support"]) == 1


def test_compute_levels_empty_inputs(calculation_engine):
    assert calculation_engine.compute_levels({}, spot=100.0) == []
    assert calculation_engine.compute_levels(_level_map(), spot=0) == []
    assert calculation_engine.compute_levels({100.0: 0.0}, spot=95.0) == []


def test_compute_levels_only_resistance_when_no_support(calculation_engine):
    levels = calculation_engine.compute_levels({105.0: 5e6, 110.0: 3e6}, spot=100.0)
    assert all(lv.kind == "resistance" for lv in levels)
