"""Skeleton smoke testi — uygulama boot olur ve /health çalışır."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_router_stub_wired(client: TestClient) -> None:
    # Router toplama (Bölüm 6.2) doğru bağlandı mı — bir stub endpoint erişilebilir mi?
    res = client.get("/api/dashboard/_status")
    assert res.status_code == 200
    assert res.json()["module"] == "dashboard"
