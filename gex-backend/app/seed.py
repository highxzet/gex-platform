"""Başlangıç verisi — sembol evreni (S&P 500 + NASDAQ-100) ve test kullanıcısı.

Çalıştırma:
    python -m app.seed                # evreni yükler, varsayılan takip setini aktif eder
    python -m app.seed --activate-all # TÜM evreni aktif eder (dikkat: tarama uzun sürer)

`is_active` = "zamanlanmış iş bu sembolü periyodik hesaplasın mı" anlamına gelir.
Aktif olmayan semboller yine aranabilir ve izleme listesine eklenebilir.
"""
from __future__ import annotations

import argparse
import logging

from sqlalchemy import select

from app.core.logging_config import setup_logging
from app.core.security import hash_password
from app.data.universe import UNIVERSE
from app.database import SessionLocal
from app.models import Symbol, User

logger = logging.getLogger(__name__)

DEFAULT_USER_EMAIL = "kurucu@gexplatform.com"
DEFAULT_USER_PASSWORD = "gexdev2026"  # yalnızca yerel geliştirme

# Varsayılan olarak periyodik hesaplanan set: en likit opsiyon piyasaları
DEFAULT_TRACKED = [
    "SPY", "QQQ",  # ETF'ler (evrende yoksa atlanır)
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD",
    "JPM", "BAC", "WFC", "C", "GS", "MS",
]


def seed_universe(db) -> tuple[int, int]:
    """Evreni yükler/günceller. (yeni, güncellenen) döner."""
    existing = {s.ticker: s for s in db.scalars(select(Symbol))}
    added = updated = 0

    for ticker, name, sector, indices in UNIVERSE:
        current = existing.get(ticker)
        if current is None:
            db.add(
                Symbol(
                    ticker=ticker,
                    company_name=name or None,
                    sector=sector or None,
                    indices=indices,
                    is_active=False,  # evren varsayılan olarak PASİF (aranabilir ama taranmaz)
                )
            )
            added += 1
        else:
            changed = False
            if name and current.company_name != name:
                current.company_name = name
                changed = True
            if sector and current.sector != sector:
                current.sector = sector
                changed = True
            if current.indices != indices:
                current.indices = indices
                changed = True
            if changed:
                updated += 1

    db.commit()
    return added, updated


def set_tracked(db, tickers: list[str] | None, activate_all: bool = False) -> int:
    """Periyodik taranacak sembolleri belirler."""
    if activate_all:
        count = 0
        for symbol in db.scalars(select(Symbol)):
            symbol.is_active = True
            count += 1
        db.commit()
        return count

    wanted = {t.upper() for t in (tickers or DEFAULT_TRACKED)}
    count = 0
    for symbol in db.scalars(select(Symbol)):
        should = symbol.ticker in wanted
        if symbol.is_active != should:
            symbol.is_active = should
        if should:
            count += 1
    db.commit()
    return count


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
    parser = argparse.ArgumentParser(description="GEX sembol evrenini yükler")
    parser.add_argument("--activate-all", action="store_true", help="tüm evreni periyodik taramaya al")
    args = parser.parse_args()

    setup_logging()
    db = SessionLocal()
    try:
        added, updated = seed_universe(db)
        tracked = set_tracked(db, None, activate_all=args.activate_all)
        user_added = seed_user(db)
        total = len(list(db.scalars(select(Symbol))))

        print(f"Evren      : {total} sembol ({added} yeni, {updated} güncellendi)")
        print(f"Takip edilen: {tracked} sembol (is_active=true)")
        print(f"Kullanıcı  : {'eklendi' if user_added else 'zaten vardı'} ({DEFAULT_USER_EMAIL})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
