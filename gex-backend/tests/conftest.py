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
