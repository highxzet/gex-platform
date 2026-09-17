"""SQLAlchemy engine ve session yönetimi.

Build Spec Bölüm 6.4 — `get_db` FastAPI dependency olarak enjekte edilir.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # kopmuş bağlantıları otomatik tespit et
    pool_size=5,
    max_overflow=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Tüm ORM modellerinin temel sınıfı."""


def get_db() -> Generator[Session, None, None]:
    """Request başına bir DB session açar, bitince kapatır (Bölüm 6.4)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
