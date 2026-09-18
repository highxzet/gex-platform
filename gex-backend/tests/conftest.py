"""Pytest fixture'ları — Build Spec Bölüm 13.2.

Entegrasyon testleri AYRI bir test veritabanında (TEST_DATABASE_URL) çalışır;
her test kendi transaction'ında izole edilir ve sonunda geri alınır.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import GexByStrike, GexSummary, PriceSnapshot, Symbol, User, WatchlistItem
from app.services.calculation_engine import CalculationEngine


# ---------- Saf hesaplama (DB gerektirmez) ----------
@pytest.fixture
def calculation_engine() -> CalculationEngine:
    return CalculationEngine(risk_free_rate=0.05)


# ---------- Veritabanı ----------
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(settings.test_database_url, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Session:
    """Her test kendi transaction'ında; sonunda rollback -> testler birbirini etkilemez."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, future=True)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """get_db bağımlılığı test session'ı ile değiştirilir (Bölüm 6.4)."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- Veri fixture'ları ----------
TEST_EMAIL = "test@gexplatform.com"
TEST_PASSWORD = "testpass123"


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        email=TEST_EMAIL,
        password_hash=hash_password(TEST_PASSWORD),
        display_name="test kullanıcı",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seeded_gex_data(db_session: Session, test_user: User) -> Symbol:
    """Bir sembol + fiyat + GEX özeti + strike verisi + izleme listesi kaydı."""
    symbol = Symbol(ticker="TST", company_name="Test Corp.", sector="Test")
    db_session.add(symbol)
    db_session.flush()

    run_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    db_session.add(
        PriceSnapshot(symbol_id=symbol.id, spot_price=100, daily_change_pct=1.5, provider="test")
    )
    db_session.add(
        GexSummary(
            symbol_id=symbol.id,
            total_net_gex=330000,
            gamma_flip_strike=100.54,
            call_wall_strike=105,
            put_wall_strike=95,
            regime="negative",
            spot_price_at_calc=100,
            calculation_run_id=run_id,
            computed_at=now,
        )
    )
    # geçmiş nokta (zaman serisi testi için)
    db_session.add(
        GexSummary(
            symbol_id=symbol.id,
            total_net_gex=250000,
            gamma_flip_strike=99.0,
            call_wall_strike=105,
            put_wall_strike=95,
            regime="negative",
            spot_price_at_calc=98,
            calculation_run_id=uuid.uuid4(),
            computed_at=now - timedelta(days=1),
        )
    )
    for strike, call_gex, put_gex in [(95, 200000, -360000), (100, 1200000, -1080000), (105, 450000, -80000)]:
        db_session.add(
            GexByStrike(
                symbol_id=symbol.id,
                strike=strike,
                expiry=(now + timedelta(days=30)).date(),
                call_gex=call_gex,
                put_gex=put_gex,
                net_gex=call_gex + put_gex,
                calculation_run_id=run_id,
            )
        )
    db_session.add(WatchlistItem(user_id=test_user.id, symbol_id=symbol.id, sort_order=0))
    db_session.commit()
    db_session.refresh(symbol)
    return symbol


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
