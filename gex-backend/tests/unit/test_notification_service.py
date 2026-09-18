"""Bildirim servisi testleri — Build Spec Bölüm 12.5.

KRİTİK KURAL: send_email_safe ASLA istisna yükseltmez; e-posta hatası
uygulama içi bildirimi etkilemez.
"""
from __future__ import annotations

import smtplib

from app.services.notification_service import _mask_email, send_email_safe


def test_mask_email_hides_local_part():
    """Bölüm 14.5: loglarda e-posta maskelenir."""
    assert _mask_email("kurucu@gexplatform.com") == "k***@gexplatform.com"
    assert _mask_email("") == "***"


def test_returns_false_when_smtp_not_configured(db_session, test_user, monkeypatch):
    monkeypatch.setattr("app.services.notification_service.settings.smtp_host", None)
    assert send_email_safe(db_session, test_user.id, "mesaj") is False


def test_returns_false_for_unknown_user(db_session, monkeypatch):
    import uuid

    monkeypatch.setattr("app.services.notification_service.settings.smtp_host", "smtp.test")
    assert send_email_safe(db_session, uuid.uuid4(), "mesaj") is False


def test_sends_email_when_configured(db_session, test_user, monkeypatch):
    sent = {}

    class _FakeSMTP:
        def __init__(self, host, port, timeout=10):
            sent["host"] = host
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def starttls(self):
            sent["tls"] = True
        def login(self, u, p):
            sent["login"] = u
        def send_message(self, msg):
            sent["to"] = msg["To"]
            sent["body"] = msg.get_content().strip()

    monkeypatch.setattr("app.services.notification_service.settings.smtp_host", "smtp.test")
    monkeypatch.setattr("app.services.notification_service.settings.smtp_username", "user")
    monkeypatch.setattr("app.services.notification_service.settings.smtp_password", "pass")
    monkeypatch.setattr("app.services.notification_service.smtplib.SMTP", _FakeSMTP)

    assert send_email_safe(db_session, test_user.id, "JPM: test uyarisi") is True
    assert sent["to"] == test_user.email
    assert sent["body"] == "JPM: test uyarisi"
    assert sent["tls"] is True


def test_never_raises_on_smtp_failure(db_session, test_user, monkeypatch):
    """E-posta patlasa bile istisna sızmaz (Bölüm 12.5)."""
    def _boom(*args, **kwargs):
        raise smtplib.SMTPException("sunucu yok")

    monkeypatch.setattr("app.services.notification_service.settings.smtp_host", "smtp.test")
    monkeypatch.setattr("app.services.notification_service.smtplib.SMTP", _boom)

    assert send_email_safe(db_session, test_user.id, "mesaj") is False
