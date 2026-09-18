"""Veri kaynağı sağlık kontrolü — Build Spec Bölüm 9.1 / 9.5."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import DataSourceStatus
from app.providers.base import MarketDataProvider

logger = logging.getLogger(__name__)

PROBE_SYMBOL = "JPM"


def data_source_healthcheck_job(db: Session, provider: MarketDataProvider) -> str:
    """Sağlayıcıyı tek bir sembolle yoklar ve `data_source_status`'a yazar."""
    source_name = f"{provider.get_provider_name()}_fiyat"
    status = "healthy"
    last_error: str | None = None
    last_success: datetime | None = None

    try:
        quote = provider.get_price(PROBE_SYMBOL)
        if quote.spot_price <= 0:
            raise ValueError("geçersiz fiyat döndü")
        last_success = datetime.now(timezone.utc)
    except Exception as e:  # noqa: BLE001
        status = "down"
        last_error = str(e)[:500]
        logger.error("Veri kaynağı sağlık kontrolü başarısız: %s", e)

    db.add(
        DataSourceStatus(
            source_name=source_name,
            status=status,
            last_success_at=last_success,
            last_error=last_error,
        )
    )
    db.commit()
    return status
