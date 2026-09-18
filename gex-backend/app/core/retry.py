"""Yeniden deneme (retry) mantığı — Build Spec Bölüm 4.5."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def fetch_with_retry(
    fetch_fn: Callable[[], T],
    max_retries: int | None = None,
    backoff_seconds: int | None = None,
    label: str = "veri çekme",
) -> T:
    """Artan bekleme süresiyle (linear backoff) yeniden dener.

    Tüm denemeler başarısız olursa son hatayı yükseltir — çağıran katman
    kısmi başarısızlık kuralını (Bölüm 4.5) uygular.
    """
    retries = max_retries if max_retries is not None else settings.max_fetch_retries
    backoff = backoff_seconds if backoff_seconds is not None else settings.fetch_retry_backoff_seconds

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return fetch_fn()
        except Exception as e:  # noqa: BLE001 — sağlayıcı her tür hata fırlatabilir
            last_error = e
            logger.warning("%s denemesi %d/%d başarısız: %s", label, attempt, retries, e)
            if attempt < retries:
                time.sleep(backoff * attempt)

    logger.error("Tüm denemeler başarısız oldu (%s): %s", label, last_error)
    assert last_error is not None
    raise last_error
