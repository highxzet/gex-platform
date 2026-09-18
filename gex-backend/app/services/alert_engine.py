"""Uyarı değerlendirme motoru — Build Spec Bölüm 12.

Her koşul türünün kendi değerlendirme fonksiyonu vardır. Motor, veritabanına
yalnızca tetiklenen uyarılar için yazar (bildirim + last_triggered_at).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alert, GexSummary, Notification, Symbol
from app.repositories import gex_repository as gex_repo
from app.services import notification_service

logger = logging.getLogger(__name__)

Evaluator = Callable[..., bool]


# ---------- Bölüm 12.1: koşul değerlendiricileri ----------
def evaluate_flip_distance(alert: Alert, current: GexSummary, previous: GexSummary | None = None) -> bool:
    """Spot fiyat, flip noktasına eşik değerinden daha yakınsa tetiklenir."""
    if current.gamma_flip_strike is None:
        return False
    distance = abs(float(current.spot_price_at_calc) - float(current.gamma_flip_strike))
    return distance <= float(alert.threshold_value)


def evaluate_regime_change(alert: Alert, current: GexSummary, previous: GexSummary | None = None) -> bool:
    """Rejim önceki hesaplamadan farklıysa tetiklenir."""
    if previous is None:
        return False
    return current.regime != previous.regime and current.regime != "unknown"


def evaluate_gex_pct_change(alert: Alert, current: GexSummary, previous: GexSummary | None = None) -> bool:
    """Net GEX, önceki ölçümden eşik yüzdesinden fazla değiştiyse tetiklenir."""
    if previous is None or float(previous.total_net_gex) == 0:
        return False
    prev = float(previous.total_net_gex)
    curr = float(current.total_net_gex)
    pct_change = abs(curr - prev) / abs(prev) * 100
    return pct_change >= float(alert.threshold_value)


def evaluate_price_level(alert: Alert, current: GexSummary, previous: GexSummary | None = None) -> bool:
    """Spot fiyat belirlenen seviyeyi geçtiyse tetiklenir."""
    return float(current.spot_price_at_calc) >= float(alert.threshold_value)


EVALUATORS: dict[str, Evaluator] = {
    "flip_distance": evaluate_flip_distance,
    "regime_change": evaluate_regime_change,
    "gex_pct_change": evaluate_gex_pct_change,
    "price_level": evaluate_price_level,
}

# Önceki özete ihtiyaç duyan koşullar (spec'teki __code__.co_argcount hilesi yerine
# açık ve okunabilir bir küme)
NEEDS_PREVIOUS = {"regime_change", "gex_pct_change"}


# ---------- Bölüm 12.4.1: bildirim metni ----------
def build_alert_message(alert: Alert, symbol: Symbol, summary: GexSummary) -> str:
    threshold = float(alert.threshold_value)
    templates = {
        "flip_distance": f"{symbol.ticker}: Flip noktasına {threshold:g}$ kaldı",
        "regime_change": f"{symbol.ticker}: Gamma rejimi değişti — şimdi {summary.regime}",
        "gex_pct_change": f"{symbol.ticker}: Net GEX %{threshold:g} değişti",
        "price_level": f"{symbol.ticker}: Fiyat {threshold:g}$ seviyesini geçti",
    }
    return templates[alert.condition_type]


# ---------- Bölüm 12.4: tetikleme ----------
def trigger_alert(db: Session, alert: Alert, symbol: Symbol, summary: GexSummary) -> Notification:
    message = build_alert_message(alert, symbol, summary)

    notification = Notification(
        user_id=alert.user_id,
        alert_id=alert.id,
        message=message,
        related_symbol_id=alert.symbol_id,
    )
    db.add(notification)
    alert.last_triggered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notification)

    # E-posta hatası in-app bildirimi ETKİLEMEZ (Bölüm 12.5 kritik kuralı)
    if "email" in (alert.channels or []):
        notification_service.send_email_safe(db, alert.user_id, message)

    return notification


# ---------- Bölüm 12.2: orkestrasyon ----------
def evaluate_alerts(db: Session) -> int:
    """Aktif tüm uyarıları değerlendirir; tetiklenen bildirim sayısını döndürür."""
    alerts = list(db.scalars(select(Alert).where(Alert.enabled.is_(True))))
    cooldown = timedelta(minutes=settings.alert_cooldown_minutes)
    now = datetime.now(timezone.utc)
    triggered_count = 0

    for alert in alerts:
        current = gex_repo.get_latest_summary(db, alert.symbol_id)
        if current is None:
            continue

        # Bölüm 12.3: sessiz pencere — bildirim yağmurunu önler
        if alert.last_triggered_at is not None:
            last = alert.last_triggered_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if now - last < cooldown:
                continue

        previous = None
        if alert.condition_type in NEEDS_PREVIOUS:
            previous = gex_repo.get_previous_summary(db, alert.symbol_id, current.computed_at)

        evaluator = EVALUATORS.get(alert.condition_type)
        if evaluator is None:
            logger.warning("Bilinmeyen uyarı koşulu: %s", alert.condition_type)
            continue

        if evaluator(alert, current, previous):
            symbol = db.get(Symbol, alert.symbol_id)
            if symbol is None:
                continue
            trigger_alert(db, alert, symbol, current)
            triggered_count += 1
            logger.info("Uyarı tetiklendi: %s / %s", symbol.ticker, alert.condition_type)

    return triggered_count
