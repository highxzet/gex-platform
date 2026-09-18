"""ABD piyasa saatleri farkındalığı — Build Spec Bölüm 4.7.

Piyasa kapalıyken gereksiz API çağrısı yapılmaz (hem maliyet hem rate limit).
"""
from __future__ import annotations

from datetime import datetime

import pytz

ET = pytz.timezone("America/New_York")


def is_market_open(now: datetime | None = None) -> bool:
    """ABD hisse piyasası açık mı (hafta içi 09:30–16:00 ET).

    Not: Resmi tatiller bu kontrole dahil değildir (MVP kapsamı). Tatil günlerinde
    veri çekimi boş döner ve kısmi başarısızlık olarak loglanır.
    """
    current = now.astimezone(ET) if now is not None else datetime.now(ET)

    if current.weekday() >= 5:  # 5=cumartesi, 6=pazar
        return False

    market_open = current.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = current.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= current <= market_close
