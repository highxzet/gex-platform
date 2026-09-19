"""APScheduler kurulumu — Build Spec Bölüm 9.3.

Piyasa açıkken her N dakikada bir veri çekilir + uyarılar değerlendirilir;
kapalıyken çekim atlanır (Bölüm 4.7 — maliyet ve rate limit).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.core.market_hours import is_market_open
from app.database import SessionLocal
from app.jobs.cleanup_job import cleanup_job
from app.jobs.eod_snapshot_job import eod_snapshot_job
from app.jobs.fetch_and_calculate_job import fetch_and_calculate_job
from app.jobs.healthcheck_job import data_source_healthcheck_job
from app.providers import get_provider
from app.services.alert_engine import evaluate_alerts
from app.services.calculation_engine import CalculationEngine

logger = logging.getLogger(__name__)


def _fetch_and_alerts() -> None:
    if not is_market_open():
        logger.debug("Piyasa kapalı — veri çekme atlandı")
        return
    db = SessionLocal()
    try:
        fetch_and_calculate_job(
            db, get_provider(), CalculationEngine(), max_workers=settings.fetch_max_workers
        )
        triggered = evaluate_alerts(db)
        if triggered:
            logger.info("%d uyarı tetiklendi", triggered)
    except Exception:  # noqa: BLE001 — zamanlanmış iş sessizce ölmemeli (Bölüm 9.5)
        logger.exception("fetch_and_calculate döngüsü başarısız")
    finally:
        db.close()


def _scan_universe() -> None:
    """Geniş evren taraması: yalnızca özet satırı yazar (detay YOK).

    518 sembol × ~1600 opsiyon satırı her döngüde saklanamaz; bu yüzden
    tarama sembol başına tek bir `gex_summary` satırı üretir (Bölüm 18.5).
    """
    if not is_market_open():
        logger.debug("Piyasa kapalı — evren taraması atlandı")
        return
    db = SessionLocal()
    try:
        fetch_and_calculate_job(
            db,
            get_provider(),
            CalculationEngine(),
            detail=False,
            max_workers=settings.fetch_max_workers,
        )
    except Exception:  # noqa: BLE001
        logger.exception("evren taraması başarısız")
    finally:
        db.close()


def _eod_snapshot() -> None:
    """Kapanış sonrası günlük anlık görüntü.

    Piyasa saati kontrolü YAPMAZ — zaten kapanıştan sonra çalışacak şekilde
    zamanlanmıştır ve hafta sonu çalışsa bile o günün son verisini kaydeder.
    """
    db = SessionLocal()
    try:
        eod_snapshot_job(db, get_provider(), CalculationEngine())
    except Exception:  # noqa: BLE001
        logger.exception("eod_snapshot_job başarısız")
    finally:
        db.close()


def _cleanup() -> None:
    db = SessionLocal()
    try:
        cleanup_job(db)
    except Exception:  # noqa: BLE001
        logger.exception("cleanup_job başarısız")
    finally:
        db.close()


def _healthcheck() -> None:
    db = SessionLocal()
    try:
        data_source_healthcheck_job(db, get_provider())
    except Exception:  # noqa: BLE001
        logger.exception("healthcheck_job başarısız")
    finally:
        db.close()


def setup_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        _fetch_and_alerts,
        IntervalTrigger(minutes=settings.fetch_interval_minutes),
        id="fetch_and_calculate",
        max_instances=1,
        coalesce=True,
    )
    if settings.scan_enabled:
        scheduler.add_job(
            _scan_universe,
            IntervalTrigger(minutes=settings.scan_interval_minutes),
            id="scan_universe",
            max_instances=1,
            coalesce=True,
        )

    if settings.eod_snapshot_enabled:
        scheduler.add_job(
            _eod_snapshot,
            CronTrigger(day_of_week="mon-fri", hour=settings.eod_snapshot_hour_et, minute=15),
            id="eod_snapshot",
            max_instances=1,
        )

    scheduler.add_job(
        _cleanup,
        CronTrigger(hour=settings.cleanup_hour_et, minute=0),
        id="cleanup",
        max_instances=1,
    )
    scheduler.add_job(
        _healthcheck,
        IntervalTrigger(minutes=5),
        id="healthcheck",
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    logger.info(
        "Zamanlayıcı başlatıldı: fetch=%ddk, healthcheck=5dk, cleanup=%02d:00",
        settings.fetch_interval_minutes,
        settings.cleanup_hour_et,
    )
    return scheduler
