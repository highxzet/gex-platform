"""Skeleton smoke testi — uygulama boot olur ve /health çalışır."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_routers_are_wired(client: TestClient) -> None:
    """Router toplama (Bölüm 6.2) doğru bağlandı mı.

    /api/dashboard var ve kimlik doğrulama istiyor (404 değil, 401).
    """
    res = client.get("/api/dashboard")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "NOT_AUTHENTICATED"
