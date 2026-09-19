"""GEX seviyelerinin fiyat tarafından "saygı görüp görmediğini" ölçen analiz.

DÜRÜSTLÜK NOTU — bu bir GEX BACKTEST'İ DEĞİLDİR:
  * Geçmiş opsiyon zinciri verimiz yok (yfinance yalnızca güncel zinciri verir),
    dolayısıyla "o gün GEX seviyesi neredeydi" bilinemiyor.
  * Bu analiz, BUGÜNKÜ seviyeleri geçmiş fiyat hareketiyle karşılaştırır.
    Yani "bu fiyat bölgesi tarihsel olarak dönüm noktası mıydı" sorusunu yanıtlar,
    "GEX bunu önceden bildi mi" sorusunu DEĞİL.
  * Bu yüzden her ölçüm, aynı aralıktaki RASTGELE seviyelerden oluşan bir
    kontrol grubuyla (baseline) birlikte raporlanır. GEX seviyeleri rastgeleden
    daha iyi tutmuyorsa, bu da anlamlı bir (negatif) sonuçtur.

Gerçek edge kanıtı için günlük GEX anlık görüntüleri biriktirilmeli (eod_snapshot_job).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.providers.base import Candle


@dataclass
class LevelStats:
    label: str
    kind: str
    price: float
    touches: int
    holds: int
    hold_rate: float | None  # None = yeterli dokunuş yok


@dataclass
class BacktestResult:
    symbol: str
    days: int
    forward_days: int
    min_touches: int
    levels: list[LevelStats]
    baseline_hold_rate: float | None
    baseline_samples: int
    verdict: str


def _touches_and_holds(
    candles: list[Candle], level: float, kind: str, forward_days: int
) -> tuple[int, int]:
    """Bir fiyat seviyesine dokunuş ve 'tutma' sayısını hesaplar.

    Dokunuş: o günün low..high aralığı seviyeyi içeriyorsa.
    Tutma (direnç): dokunuş günü seviyenin ALTINDA kapandı VE `forward_days`
      sonra hâlâ altında. (Destek için tersi.)
    """
    touches = holds = 0
    n = len(candles)
    for i, c in enumerate(candles):
        if i + forward_days >= n:
            break
        if not (c.low <= level <= c.high):
            continue
        touches += 1
        future_close = candles[i + forward_days].close
        if kind == "resistance":
            if c.close < level and future_close < level:
                holds += 1
        else:  # support / flip
            if c.close > level and future_close > level:
                holds += 1
    return touches, holds


def _baseline(
    candles: list[Candle], forward_days: int, samples: int, seed: int
) -> tuple[float | None, int]:
    """Kontrol grubu: aynı fiyat aralığında rastgele seviyeler.

    GEX seviyelerinin anlamlı olup olmadığını söyleyebilmek için referans şart —
    fiyat her seviyede bir miktar 'tutar', asıl soru GEX'in bundan iyi olup olmadığı.
    """
    lows = [c.low for c in candles]
    highs = [c.high for c in candles]
    if not lows:
        return None, 0
    lo, hi = min(lows), max(highs)
    if hi <= lo:
        return None, 0

    rng = random.Random(seed)
    total_touches = total_holds = 0
    used = 0
    for _ in range(samples):
        level = rng.uniform(lo, hi)
        kind = "resistance" if rng.random() < 0.5 else "support"
        t, h = _touches_and_holds(candles, level, kind, forward_days)
        if t == 0:
            continue
        total_touches += t
        total_holds += h
        used += 1

    if total_touches == 0:
        return None, used
    return total_holds / total_touches, used


def _round_number_baseline(
    candles: list[Candle], forward_days: int, step: float, seed: int
) -> tuple[float | None, int]:
    """DAHA SERT kontrol: aynı aralıktaki YUVARLAK sayılar (strike ızgarası).

    GEX seviyeleri zaten hep yuvarlak sayıdır (strike'lar 5/10 katı). Eğer etki
    sadece "yuvarlak sayı" olmaktan geliyorsa, GEX'in seçimi bir şey katmıyor
    demektir. Bu kontrol tam olarak onu ayrıştırır.
    """
    lows = [c.low for c in candles]
    highs = [c.high for c in candles]
    if not lows or step <= 0:
        return None, 0
    lo, hi = min(lows), max(highs)

    grid = []
    x = (int(lo / step) + 1) * step
    while x < hi:
        grid.append(round(x, 4))
        x += step
    if not grid:
        return None, 0

    rng = random.Random(seed)
    total_t = total_h = 0
    for level in grid:
        kind = "resistance" if rng.random() < 0.5 else "support"
        t, h = _touches_and_holds(candles, level, kind, forward_days)
        total_t += t
        total_h += h
    if total_t == 0:
        return None, len(grid)
    return total_h / total_t, len(grid)


def analyze_levels(
    symbol: str,
    candles: list[Candle],
    levels: list[tuple[str, str, float]],  # (label, kind, price)
    forward_days: int = 5,
    min_touches: int = 3,
    baseline_samples: int = 200,
) -> BacktestResult:
    """Her GEX seviyesi için dokunuş/tutma oranını ve kontrol grubunu hesaplar."""
    stats: list[LevelStats] = []
    for label, kind, price in levels:
        touches, holds = _touches_and_holds(candles, price, kind, forward_days)
        stats.append(
            LevelStats(
                label=label,
                kind=kind,
                price=price,
                touches=touches,
                holds=holds,
                hold_rate=(holds / touches) if touches >= min_touches else None,
            )
        )

    base_rate, base_used = _baseline(candles, forward_days, baseline_samples, seed=hash(symbol) & 0xFFFF)

    measured = [s for s in stats if s.hold_rate is not None]
    # DOKUNUŞ-AĞIRLIKLI oran kullanılır: 3 dokunuşlu bir seviyeyle 30 dokunuşlu
    # seviyeyi eşit saymak yanıltıcı olur (ağırlıksız ortalama bunu yapardı).
    tot_t = sum(s.touches for s in measured)
    tot_h = sum(s.holds for s in measured)

    if not measured:
        verdict = (
            f"Yeterli veri yok: hiçbir seviyede en az {min_touches} dokunuş yok. "
            "Seviyeler güncel fiyattan uzak olabilir ya da geçmiş penceresi kısa."
        )
    elif base_rate is None:
        verdict = "Kontrol grubu hesaplanamadı."
    else:
        avg = (tot_h / tot_t) if tot_t else 0.0
        diff = (avg - base_rate) * 100
        if diff > 5:
            verdict = (
                f"GEX seviyeleri kontrol grubundan %{diff:.1f} daha iyi tuttu "
                f"({avg:.0%} vs {base_rate:.0%}). Umut verici ama bu bir GEX backtest'i DEĞİL "
                "(bugünkü seviyeler geçmişe uygulandı) — kesin yargı için GEX geçmişi biriktirilmeli."
            )
        elif diff < -5:
            verdict = (
                f"GEX seviyeleri kontrol grubundan %{abs(diff):.1f} daha KÖTÜ tuttu "
                f"({avg:.0%} vs {base_rate:.0%}). Bu fiyat bölgeleri rastgele seviyelerden ayrışmıyor."
            )
        else:
            verdict = (
                f"GEX seviyeleri kontrol grubundan ayırt edilemiyor "
                f"({avg:.0%} vs {base_rate:.0%}, fark %{diff:+.1f}). "
                "Yani bu testte ölçülebilir bir üstünlük YOK."
            )

    return BacktestResult(
        symbol=symbol,
        days=len(candles),
        forward_days=forward_days,
        min_touches=min_touches,
        levels=stats,
        baseline_hold_rate=base_rate,
        baseline_samples=base_used,
        verdict=verdict,
    )
