"""Alert Engine testleri — Build Spec Bölüm 13.4.

Değerlendirici fonksiyonlar saf olduğu için çoğu test DB gerektirmez;
cooldown ve tetikleme akışı gerçek session ile doğrulanır.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models import Alert, GexSummary, Notification, Symbol
from app.services.alert_engine import (
    build_alert_message,
    evaluate_alerts,
    evaluate_flip_distance,
    evaluate_gex_pct_change,
    evaluate_price_level,
    evaluate_regime_change,
)


def _alert(condition_type: str, threshold: float) -> Alert:
    return Alert(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        symbol_id=uuid.uuid4(),
        condition_type=condition_type,
        threshold_value=threshold,
        channels=["in_app"],
        enabled=True,
    )


def _summary(spot: float, flip: float | None = None, regime: str = "positive", net_gex: float = 1000.0) -> GexSummary:
    return GexSummary(
        symbol_id=uuid.uuid4(),
        total_net_gex=net_gex,
        gamma_flip_strike=flip,
        call_wall_strike=None,
        put_wall_strike=None,
        regime=regime,
        spot_price_at_calc=spot,
        calculation_run_id=uuid.uuid4(),
    )


# ---------- flip_distance ----------
def test_flip_distance_triggers_when_close():
    alert = _alert("flip_distance", 0.50)
    summary = _summary(spot=141.20, flip=141.50)  # fark 0.30
    assert evaluate_flip_distance(alert, summary) is True


def test_flip_distance_does_not_trigger_when_far():
    alert = _alert("flip_distance", 0.50)
    summary = _summary(spot=138.00, flip=141.50)  # fark 3.50
    assert evaluate_flip_distance(alert, summary) is False


def test_flip_distance_false_when_no_flip():
    alert = _alert("flip_distance", 0.50)
    assert evaluate_flip_distance(alert, _summary(spot=100, flip=None)) is False


# ---------- regime_change ----------
def test_regime_change_triggers_on_change():
    alert = _alert("regime_change", 0)
    assert evaluate_regime_change(alert, _summary(100, regime="negative"), _summary(100, regime="positive")) is True


def test_regime_change_false_when_same():
    alert = _alert("regime_change", 0)
    assert evaluate_regime_change(alert, _summary(100, regime="positive"), _summary(100, regime="positive")) is False


def test_regime_change_false_without_previous():
    alert = _alert("regime_change", 0)
    assert evaluate_regime_change(alert, _summary(100, regime="negative"), None) is False


def test_regime_change_ignores_unknown():
    """'unknown'a geçiş gerçek bir rejim değişimi sayılmaz."""
    alert = _alert("regime_change", 0)
    assert evaluate_regime_change(alert, _summary(100, regime="unknown"), _summary(100, regime="positive")) is False


# ---------- gex_pct_change ----------
def test_gex_pct_change_triggers_above_threshold():
    alert = _alert("gex_pct_change", 25)
    assert evaluate_gex_pct_change(alert, _summary(100, net_gex=1400), _summary(100, net_gex=1000)) is True


def test_gex_pct_change_below_threshold():
    alert = _alert("gex_pct_change", 25)
    assert evaluate_gex_pct_change(alert, _summary(100, net_gex=1100), _summary(100, net_gex=1000)) is False


def test_gex_pct_change_handles_zero_previous():
    """Sıfıra bölme korunur."""
    alert = _alert("gex_pct_change", 25)
    assert evaluate_gex_pct_change(alert, _summary(100, net_gex=500), _summary(100, net_gex=0)) is False


def test_gex_pct_change_without_previous():
    alert = _alert("gex_pct_change", 25)
    assert evaluate_gex_pct_change(alert, _summary(100, net_gex=500), None) is False


# ---------- price_level ----------
def test_price_level_triggers_when_above():
    assert evaluate_price_level(_alert("price_level", 145), _summary(spot=146)) is True


def test_price_level_false_when_below():
    assert evaluate_price_level(_alert("price_level", 145), _summary(spot=144)) is False


# ---------- mesaj üretimi (Bölüm 12.4.1) ----------
@pytest.mark.parametrize(
    "condition,expected_fragment",
    [
        ("flip_distance", "Flip noktasına"),
        ("regime_change", "Gamma rejimi değişti"),
        ("gex_pct_change", "Net GEX"),
        ("price_level", "seviyesini geçti"),
    ],
)
def test_build_alert_message(condition, expected_fragment):
    symbol = Symbol(ticker="JPM", company_name="JPMorgan")
    message = build_alert_message(_alert(condition, 0.5), symbol, _summary(100, regime="negative"))
    assert message.startswith("JPM:")
    assert expected_fragment in message


# ---------- Cooldown ve tetikleme akışı (DB) ----------
def test_alert_triggers_and_creates_notification(db_session, test_user, seeded_gex_data):
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,  # spot 100 -> tetiklenir
        channels=["in_app"],
    )
    db_session.add(alert)
    db_session.commit()

    assert evaluate_alerts(db_session) == 1
    notifications = db_session.query(Notification).filter(Notification.alert_id == alert.id).all()
    assert len(notifications) == 1
    assert "TST" in notifications[0].message
    db_session.refresh(alert)
    assert alert.last_triggered_at is not None


def test_alert_does_not_retrigger_within_cooldown(db_session, test_user, seeded_gex_data):
    """Bölüm 12.3: 30 dakikalık sessiz pencere bildirim yağmurunu önler."""
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["in_app"],
        last_triggered_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    db_session.add(alert)
    db_session.commit()

    assert evaluate_alerts(db_session) == 0
    assert db_session.query(Notification).filter(Notification.alert_id == alert.id).count() == 0


def test_alert_retriggers_after_cooldown(db_session, test_user, seeded_gex_data):
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["in_app"],
        last_triggered_at=datetime.now(timezone.utc) - timedelta(minutes=45),
    )
    db_session.add(alert)
    db_session.commit()
    assert evaluate_alerts(db_session) == 1


def test_disabled_alert_is_skipped(db_session, test_user, seeded_gex_data):
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["in_app"],
        enabled=False,
    )
    db_session.add(alert)
    db_session.commit()
    assert evaluate_alerts(db_session) == 0


# ---------- Kalan dallar: e-posta kanalı, bilinmeyen koşul, eksik veri ----------
def test_email_channel_calls_notification_service(db_session, test_user, seeded_gex_data, monkeypatch):
    """E-posta kanalı seçiliyse bildirim servisi çağrılır (Bölüm 12.4)."""
    sent: list[str] = []
    monkeypatch.setattr(
        "app.services.alert_engine.notification_service.send_email_safe",
        lambda db, user_id, message: sent.append(message) or True,
    )
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["in_app", "email"],
    )
    db_session.add(alert)
    db_session.commit()

    assert evaluate_alerts(db_session) == 1
    assert len(sent) == 1 and "TST" in sent[0]


def test_email_failure_does_not_rollback_in_app_notification(db_session, test_user, seeded_gex_data, monkeypatch):
    """Bölüm 12.5 kritik kuralı: e-posta hatası in-app bildirimi ETKİLEMEZ."""
    monkeypatch.setattr(
        "app.services.alert_engine.notification_service.send_email_safe",
        lambda db, user_id, message: False,
    )
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["email"],
    )
    db_session.add(alert)
    db_session.commit()

    assert evaluate_alerts(db_session) == 1
    assert db_session.query(Notification).filter(Notification.alert_id == alert.id).count() == 1


def test_alert_skipped_when_no_summary(db_session, test_user):
    """GEX özeti olmayan sembol için uyarı sessizce atlanır."""
    symbol = Symbol(ticker="NOSUM", company_name="No Summary Inc.")
    db_session.add(symbol)
    db_session.flush()
    db_session.add(
        Alert(
            user_id=test_user.id,
            symbol_id=symbol.id,
            condition_type="price_level",
            threshold_value=1,
            channels=["in_app"],
        )
    )
    db_session.commit()
    assert evaluate_alerts(db_session) == 0


def test_unknown_condition_type_is_skipped(db_session, test_user, seeded_gex_data, monkeypatch):
    """Bilinmeyen koşul türü çökmez, loglanıp atlanır.

    (DB'deki CHECK kısıtı geçersiz değeri engellediği için, kayıt geçerli
    kalır ve bunun yerine değerlendirici kaydı kaldırılır.)
    """
    monkeypatch.setattr("app.services.alert_engine.EVALUATORS", {})
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=1,
        channels=["in_app"],
    )
    db_session.add(alert)
    db_session.commit()
    assert evaluate_alerts(db_session) == 0


def test_naive_last_triggered_at_is_handled(db_session, test_user, seeded_gex_data):
    """Saat dilimi bilgisi olmayan timestamp UTC kabul edilir (cooldown karşılaştırması)."""
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=50,
        channels=["in_app"],
        last_triggered_at=datetime.utcnow() - timedelta(minutes=5),  # naive
    )
    db_session.add(alert)
    db_session.commit()
    assert evaluate_alerts(db_session) == 0  # cooldown içinde


def test_regime_change_uses_previous_summary(db_session, test_user, seeded_gex_data):
    """regime_change önceki özeti çeker (NEEDS_PREVIOUS yolu)."""
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="regime_change",
        threshold_value=0,
        channels=["in_app"],
    )
    db_session.add(alert)
    db_session.commit()
    # fixture'daki iki özet de "negative" -> değişim yok
    assert evaluate_alerts(db_session) == 0
