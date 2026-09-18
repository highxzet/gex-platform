"""Başlangıç verisi — izlenen banka sembolleri ve (opsiyonel) test kullanıcısı.

Çalıştırma:  python -m app.seed
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.logging_config import setup_logging
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Symbol, User

logger = logging.getLogger(__name__)

# Tasarımdaki izleme listesiyle uyumlu bankacılık sembolleri
BANK_SYMBOLS: list[tuple[str, str, str]] = [
    ("JPM", "JPMorgan Chase & Co.", "Bankacılık"),
    ("BAC", "Bank of America Corp.", "Bankacılık"),
    ("WFC", "Wells Fargo & Co.", "Bankacılık"),
    ("C", "Citigroup Inc.", "Bankacılık"),
    ("GS", "Goldman Sachs Group Inc.", "Yatırım Bankacılığı"),
    ("MS", "Morgan Stanley", "Yatırım Bankacılığı"),
    ("USB", "U.S. Bancorp", "Bankacılık"),
    ("PNC", "PNC Financial Services Group", "Bankacılık"),
]

DEFAULT_USER_EMAIL = "kurucu@gex.local"
DEFAULT_USER_PASSWORD = "gexdev2026"  # yalnızca yerel geliştirme


def seed_symbols(db) -> int:
    added = 0
    for ticker, name, sector in BANK_SYMBOLS:
        exists = db.scalar(select(Symbol).where(Symbol.ticker == ticker))
        if exists:
            continue
        db.add(Symbol(ticker=ticker, company_name=name, sector=sector))
        added += 1
    db.commit()
    return added


def seed_user(db) -> bool:
    if db.scalar(select(User).where(User.email == DEFAULT_USER_EMAIL)):
        return False
    db.add(
        User(
            email=DEFAULT_USER_EMAIL,
            password_hash=hash_password(DEFAULT_USER_PASSWORD),
            display_name="kurucu",
            onboarding_completed=True,
        )
    )
    db.commit()
    return True


def main() -> None:
    setup_logging()
    db = SessionLocal()
    try:
        n = seed_symbols(db)
        u = seed_user(db)
        total = db.scalar(select(Symbol).where(Symbol.is_active.is_(True)).with_only_columns(Symbol.id))
        logger.info("seed tamam: %d yeni sembol, kullanıcı eklendi=%s", n, u)
        print(f"Eklenen sembol: {n}")
        print(f"Test kullanıcısı eklendi: {u}  ({DEFAULT_USER_EMAIL} / {DEFAULT_USER_PASSWORD})")
        print(f"Toplam aktif sembol: {len(list(db.scalars(select(Symbol).where(Symbol.is_active.is_(True)))))}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
