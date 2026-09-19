"""Pine Script üretici testleri."""
from __future__ import annotations

from app.services.pine_export_service import SymbolLevels, build_pine_script


def _sample() -> SymbolLevels:
    return SymbolLevels(
        ticker="NVDA", spot=219.55, call_wall=230.0, put_wall=205.0, flip=203.74,
        resistances=[220.0, 225.0], supports=[195.0, 190.0],
    )


def test_script_has_pine_v6_header():
    s = build_pine_script([_sample()])
    assert s.startswith("//@version=6")
    assert "indicator(" in s


def test_script_embeds_levels():
    s = build_pine_script([_sample()])
    assert 'syminfo.ticker == "NVDA"' in s
    assert "cw := 230" in s
    assert "pw := 205" in s
    assert "fl := 203.74" in s


def test_missing_levels_become_na():
    """Eksik seviye Pine'da `na` olmalı — 0 yazmak yanlış çizgi çizdirirdi."""
    s = build_pine_script([SymbolLevels(ticker="X", spot=10.0)])
    assert "cw := na" in s
    assert "pw := na" in s


def test_multiple_symbols_use_else_if_chain():
    a = SymbolLevels(ticker="AAA", spot=1.0, call_wall=2.0)
    b = SymbolLevels(ticker="BBB", spot=1.0, call_wall=3.0)
    s = build_pine_script([a, b])
    assert 'if syminfo.ticker == "AAA"' in s
    assert 'else if syminfo.ticker == "BBB"' in s


def test_script_declares_all_plots_and_alerts():
    s = build_pine_script([_sample()])
    for name in ("Call Wall", "Put Wall", "Gamma Flip", "1. Direnç", "1. Destek"):
        assert name in s
    assert s.count("plot(") >= 7
    assert "alertcondition(" in s


def test_number_formatting_trims_zeros():
    s = build_pine_script([SymbolLevels(ticker="X", spot=1.0, call_wall=230.0000, flip=57.3718)])
    assert "cw := 230" in s and "cw := 230.0000" not in s
    assert "fl := 57.3718" in s
