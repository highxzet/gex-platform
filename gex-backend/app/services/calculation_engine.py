"""GEX Hesaplama Motoru — Build Spec Bölüm 3 + 8.

Bu sınıf VERİTABANINA DOKUNMAZ (Bölüm 8.2): yalnızca saf hesaplama fonksiyonları
içerir, böylece birim testleri DB bağlantısı olmadan saniyeler içinde çalışır.
Veritabanına yazma işi çağıran katmanın (jobs/) sorumluluğundadır.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
from scipy.stats import norm

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
    """Bölüm 8.1'deki hesaplama motoru.

    Parametreler ortam değişkenlerinden (Bölüm 15) gelir; testler için
    doğrudan da geçilebilir.
    """

    def __init__(
        self,
        risk_free_rate: float | None = None,
        contract_multiplier: int | None = None,
        gex_move_pct: float | None = None,
        neutral_band_pct: float | None = None,
    ) -> None:
        self.risk_free_rate = risk_free_rate if risk_free_rate is not None else settings.risk_free_rate
        self.contract_multiplier = (
            contract_multiplier if contract_multiplier is not None else settings.contract_multiplier
        )
        self.gex_move_pct = gex_move_pct if gex_move_pct is not None else settings.gex_move_pct
        self.neutral_band_pct = (
            neutral_band_pct if neutral_band_pct is not None else settings.neutral_band_pct
        )

    # ---- Bölüm 3.3 — Black-Scholes gamma ----
    def black_scholes_gamma(self, S: float, K: float, T: float, sigma: float | None) -> float:  # noqa: N803
        """Γ = N'(d1) / (S · σ · √T). Geçersiz/vadesi dolmuş girdide 0.0 döner (hata fırlatmaz)."""
        if sigma is None or T is None or S is None or K is None:
            return 0.0
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return 0.0
        d1 = (np.log(S / K) + (self.risk_free_rate + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))

    # ---- Bölüm 3.2 — sağlayıcı gamma'sı varsa onu kullan ----
    def resolve_gamma(
        self,
        provided_gamma: float | None,
        S: float,  # noqa: N803
        K: float,  # noqa: N803
        T: float,  # noqa: N803
        iv: float | None,
    ) -> float | None:
        """Sağlayıcı gamma verdiyse birebir onu kullan; yoksa Black-Scholes ile hesapla.

        IV de yoksa None döner → bu satır hesaplama dışı bırakılır (Bölüm 4.4).
        """
        if provided_gamma is not None:
            return provided_gamma
        if iv is None or iv <= 0:
            return None
        return self.black_scholes_gamma(S, K, T, iv)

    # ---- Bölüm 3.4 / 3.5 — strike bazında dolar GEX ----
    def calculate_strike_gex(
        self, gamma_call: float, oi_call: int, gamma_put: float, oi_put: int, spot: float
    ) -> tuple[float, float, float]:
        """Call pozitif, put negatif katkı (Bölüm 3.5 dealer işaret konvansiyonu)."""
        factor = self.contract_multiplier * (spot**2) * self.gex_move_pct
        call_gex = gamma_call * oi_call * factor
        put_gex = -1 * gamma_put * oi_put * factor
        return call_gex, put_gex, call_gex + put_gex

    # ---- Bölüm 3.7 — gamma flip (doğrusal interpolasyon) ----
    def find_gamma_flip(
        self, strikes_sorted: list[float], cumulative_gex: list[float]
    ) -> float | None:
        """Kümülatif net GEX'in sıfırı kestiği strike. İşaret değişimi yoksa None."""
        for i in range(1, len(cumulative_gex)):
            prev_gex = cumulative_gex[i - 1]
            curr_gex = cumulative_gex[i]
            if prev_gex == 0:
                return strikes_sorted[i - 1]
            if (prev_gex < 0 < curr_gex) or (prev_gex > 0 > curr_gex):
                prev_strike = strikes_sorted[i - 1]
                curr_strike = strikes_sorted[i]
                ratio = abs(prev_gex) / (abs(prev_gex) + abs(curr_gex))
                return prev_strike + ratio * (curr_strike - prev_strike)
        return None

    def find_all_gamma_flips(
        self, strikes_sorted: list[float], cumulative_gex: list[float]
    ) -> list[float]:
        """Kümülatif net GEX'in sıfırı kestiği TÜM noktalar (interpolasyonlu).

        Gerçek veride derin OTM strike'larda gamma ~ 0 olduğundan kümülatif sıfır
        etrafında salınır ve birden fazla (çoğu anlamsız) kesişim oluşur.
        """
        flips: list[float] = []
        for i in range(1, len(cumulative_gex)):
            prev_gex = cumulative_gex[i - 1]
            curr_gex = cumulative_gex[i]
            if prev_gex == 0:
                flips.append(strikes_sorted[i - 1])
                continue
            if (prev_gex < 0 < curr_gex) or (prev_gex > 0 > curr_gex):
                prev_strike = strikes_sorted[i - 1]
                curr_strike = strikes_sorted[i]
                ratio = abs(prev_gex) / (abs(prev_gex) + abs(curr_gex))
                flips.append(prev_strike + ratio * (curr_strike - prev_strike))
        return flips

    def select_gamma_flip(
        self, strikes_sorted: list[float], cumulative_gex: list[float], spot: float
    ) -> float | None:
        """Anlamlı gamma flip noktasını seçer (bkz. GAMMA_FLIP_SELECTION).

        - "nearest_spot" (varsayılan): tüm kesişimler arasından spot'a en yakın olan.
          Gerekçe: derin OTM gürültüsü ilk kesişimi anlamsız bir strike'a kaydırır;
          spec'in Faz 2 kabul kriteri ise flip'in spot'a yakın olmasını bekler.
        - "first": Bölüm 3.7'nin birebir davranışı (ilk işaret değişimi).
        """
        if settings.gamma_flip_selection == "first":
            return self.find_gamma_flip(strikes_sorted, cumulative_gex)

        flips = self.find_all_gamma_flips(strikes_sorted, cumulative_gex)
        if not flips:
            return None
        return min(flips, key=lambda f: abs(f - spot))

    # ---- Bölüm 3.8 — call / put wall ----
    def find_walls(
        self, strike_gex_map: dict[float, float]
    ) -> tuple[float | None, float | None]:
        """Call wall: en yüksek pozitif GEX'li strike. Put wall: en negatif GEX'li strike."""
        positive = {k: v for k, v in strike_gex_map.items() if v > 0}
        negative = {k: v for k, v in strike_gex_map.items() if v < 0}
        call_wall = max(positive, key=positive.__getitem__) if positive else None
        put_wall = min(negative, key=negative.__getitem__) if negative else None
        return call_wall, put_wall

    # ---- Bölüm 3.9 — rejim ----
    def determine_regime(self, spot: float, gamma_flip: float | None) -> str:
        if gamma_flip is None:
            return "unknown"
        diff_pct = abs(spot - gamma_flip) / spot
        if diff_pct <= self.neutral_band_pct:
            return "neutral"
        return "positive" if spot > gamma_flip else "negative"

    # ---- Bölüm 8.1 — ana orkestrasyon ----
    def calculate_symbol_gex(
        self, symbol: str, spot: float, option_rows: list[dict]
    ) -> SymbolGexSummary:
        """option_rows: [{strike, expiry, call_oi, put_oi, call_gamma, put_gamma,
        call_iv, put_iv, expiry_years}, ...]

        expiry_years çağıran katman tarafından önceden hesaplanır (Bölüm 9.2).
        """
        strike_results: list[StrikeGexResult] = []
        strike_gex_map: dict[float, float] = {}

        for row in option_rows:
            gamma_call = self.resolve_gamma(
                row.get("call_gamma"), spot, row["strike"], row["expiry_years"], row.get("call_iv")
            )
            gamma_put = self.resolve_gamma(
                row.get("put_gamma"), spot, row["strike"], row["expiry_years"], row.get("put_iv")
            )
            # her iki bacak da hesaplanamıyorsa bu satırı tamamen atla (Bölüm 4.4)
            if gamma_call is None and gamma_put is None:
                continue

            call_gex, put_gex, net_gex = self.calculate_strike_gex(
                gamma_call or 0.0, row["call_oi"], gamma_put or 0.0, row["put_oi"], spot
            )
            strike_results.append(
                StrikeGexResult(row["strike"], row["expiry"], call_gex, put_gex, net_gex)
            )
            # aynı strike'ta birden fazla vade olabilir → strike bazında topla
            strike_gex_map[row["strike"]] = strike_gex_map.get(row["strike"], 0.0) + net_gex

        total_net_gex = sum(r.net_gex for r in strike_results)

        sorted_strikes = sorted(strike_gex_map.keys())
        cumulative: list[float] = []
        running = 0.0
        for s in sorted_strikes:
            running += strike_gex_map[s]
            cumulative.append(running)

        gamma_flip = self.select_gamma_flip(sorted_strikes, cumulative, spot)
        call_wall, put_wall = self.find_walls(strike_gex_map)
        regime = self.determine_regime(spot, gamma_flip)

        return SymbolGexSummary(
            symbol=symbol,
            total_net_gex=total_net_gex,
            gamma_flip_strike=gamma_flip,
            call_wall_strike=call_wall,
            put_wall_strike=put_wall,
            regime=regime,
            spot_price=spot,
            strike_results=strike_results,
        )
