"""Veri saklama (retention) temizliği — Build Spec Bölüm 5.15 / 9.4."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GexByStrike, Notification, OptionChainRaw, PriceSnapshot

logger = logging.getLogger(__name__)


def cleanup_job(db: Session) -> dict[str, int]:
    """Retention politikasını uygular; tablo başına silinen satır sayısını döndürür."""
    now = datetime.now(timezone.utc)
    deleted: dict[str, int] = {}

    plan = [
        (OptionChainRaw, OptionChainRaw.fetched_at, settings.raw_data_retention_days),
        (GexByStrike, GexByStrike.computed_at, settings.strike_gex_retention_days),
        (PriceSnapshot, PriceSnapshot.fetched_at, settings.price_snapshot_retention_days),
    ]
    for model, ts_column, days in plan:
        cutoff = now - timedelta(days=days)
        result = db.execute(delete(model).where(ts_column < cutoff))
        deleted[model.__tablename__] = result.rowcount or 0

    # Okunmuş bildirimler (okunmamışlar süresiz saklanır)
    notif_cutoff = now - timedelta(days=settings.read_notification_retention_days)
    result = db.execute(
        delete(Notification).where(
            Notification.is_read.is_(True), Notification.created_at < notif_cutoff
        )
    )
    deleted["notifications"] = result.rowcount or 0

    db.commit()
    for table, count in deleted.items():
        if count:
            logger.info("%s: %d eski kayıt silindi", table, count)
    return deleted
