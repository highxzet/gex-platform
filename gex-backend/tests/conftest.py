"""Pytest fixture'ları — Build Spec Bölüm 13.2.

Skeleton: TestClient fixture'ı hazır. Veritabanı gerektiren fixture'lar
(db_session) modeller yazıldığında (Faz 1) etkinleşir.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def calculation_engine() -> "CalculationEngine":
    """Bölüm 13.2 — DB gerektirmeyen saf hesaplama motoru fixture'ı."""
    from app.services.calculation_engine import CalculationEngine

    return CalculationEngine(risk_free_rate=0.05)
