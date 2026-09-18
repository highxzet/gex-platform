"""Bildirim servisi — Build Spec Bölüm 12.5.

KRİTİK KURAL: E-posta gönderimi başarısız olursa uygulama içi bildirim kaydı
GERİ ALINMAZ — iki kanal birbirinden bağımsızdır (Bölüm 4.5 kısmi başarısızlık
prensibiyle tutarlı).
"""
from __future__ import annotations

import logging
import smtplib
import uuid
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)


def _mask_email(email: str) -> str:
    """Loglarda e-postayı maskele (Bölüm 14.5 hassas veri kuralı)."""
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}" if local else "***"


def send_email_safe(db: Session, user_id: uuid.UUID, message: str) -> bool:
    """E-posta göndermeyi dener; başarısızlıkta ASLA istisna yükseltmez."""
    if not settings.smtp_host:
        logger.info("SMTP yapılandırılmamış, e-posta atlanıyor (in-app bildirim gönderildi)")
        return False

    user = db.get(User, user_id)
    if user is None:
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = "GEX Uyarısı"
        msg["From"] = settings.smtp_from_address
        msg["To"] = user.email
        msg.set_content(message)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        logger.info("E-posta gönderildi: %s", _mask_email(user.email))
        return True
    except Exception as e:  # noqa: BLE001 — e-posta hatası akışı bozmaz
        logger.error("E-posta gönderilemedi (user=%s): %s", _mask_email(user.email), e)
        return False
