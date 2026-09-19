"""Günlük kapanış anlık görüntüsü — ileriye dönük edge doğrulaması için.

NEDEN VAR: Geçmiş opsiyon zinciri verisi satın almadan GEX backtest'i yapılamaz.
"Bugünkü seviyeleri geçmişe uygulama" yöntemi döngüsellik içerir (yüksek OI,
fiyatın zaten takıldığı strike'larda birikir).

Bu iş her kapanışta her aktif sembol için TEK bir `gex_summary` satırı yazar
(gamma_flip / call_wall / put_wall / spot dahil). Böylece zamanla
"T gününde seviye neredeydi, T+k'da fiyat ne yaptı" sorusunu temiz biçimde
yanıtlayabileceğimiz bir veri seti birikir.

Maliyet: sembol başına günde 1 satır (139 sembol = 139 satır/gün). İhmal edilebilir.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.jobs.fetch_and_calculate_job import fetch_and_calculate_job
from app.models import CalculationRun
from app.providers.base import MarketDataProvider
from app.services.calculation_engine import CalculationEngine

logger = logging.getLogger(__name__)


def eod_snapshot_job(
    db: Session,
    provider: MarketDataProvider,
    engine: CalculationEngine | None = None,
) -> CalculationRun:
    """Tüm aktif semboller için kapanış özeti yazar (strike detayı YOK)."""
    logger.info("EOD anlık görüntü başlıyor (ileriye dönük doğrulama veri seti)")
    run = fetch_and_calculate_job(
        db,
        provider,
        engine or CalculationEngine(),
        detail=False,  # yalnızca özet — günde 1 satır/sembol
        max_workers=settings.fetch_max_workers,
    )
    logger.info(
        "EOD anlık görüntü tamamlandı: %d sembol kaydedildi, %d başarısız",
        run.symbols_succeeded,
        run.symbols_failed,
    )
    return run
