"""GEX Hesaplama Motoru — Build Spec Bölüm 3 + 8.

SKELETON: Sınıf yapısı ve arayüzü hazır; formüllerin tam implementasyonu Faz 1'de
(Bölüm 8.1 birebir) yazılacak ve Bölüm 13.3'teki birim testleriyle %100 kapsanacak.

Bu sınıf VERİTABANINA DOKUNMAZ — sadece saf hesaplama fonksiyonları içerir (Bölüm 8.2).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.config import settings


@dataclass
class StrikeGexResult:
    strike: float
    expiry: date
    call_gex: float
    put_gex: float
    net_gex: float


@dataclass
class SymbolGexSummary:
    symbol: str
    total_net_gex: float
    gamma_flip_strike: float | None
    call_wall_strike: float | None
    put_wall_strike: float | None
    regime: str
    spot_price: float
    strike_results: list[StrikeGexResult]


class CalculationEngine:
    """Bölüm 8.1'deki motorun iskeleti. Metod imzaları nihai; gövdeler Faz 1'de."""

    def __init__(self, risk_free_rate: float | None = None) -> None:
        self.risk_free_rate = risk_free_rate if risk_free_rate is not None else settings.risk_free_rate

    def black_scholes_gamma(self, S: float, K: float, T: float, sigma: float) -> float:  # noqa: N803
        raise NotImplementedError("Faz 1 — Bölüm 3.3 / 8.1")

    def calculate_strike_gex(
        self, gamma_call: float, oi_call: int, gamma_put: float, oi_put: int, spot: float
    ) -> tuple[float, float, float]:
        raise NotImplementedError("Faz 1 — Bölüm 3.4 / 8.1")

    def find_gamma_flip(
        self, strikes_sorted: list[float], cumulative_gex: list[float]
    ) -> float | None:
        raise NotImplementedError("Faz 1 — Bölüm 3.7 / 8.1")

    def find_walls(
        self, strike_gex_map: dict[float, float]
    ) -> tuple[float | None, float | None]:
        raise NotImplementedError("Faz 1 — Bölüm 3.8 / 8.1")

    def determine_regime(self, spot: float, gamma_flip: float | None) -> str:
        raise NotImplementedError("Faz 1 — Bölüm 3.9 / 8.1")

    def calculate_symbol_gex(
        self, symbol: str, spot: float, option_rows: list[dict]
    ) -> SymbolGexSummary:
        raise NotImplementedError("Faz 1 — Bölüm 8.1 ana orkestrasyon")
