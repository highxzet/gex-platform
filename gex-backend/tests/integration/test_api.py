"""API entegrasyon testleri — Build Spec Bölüm 13.5 / 13.7.

Kural: her endpoint için en az 1 başarı + 1 hata senaryosu.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import TEST_EMAIL, TEST_PASSWORD


# ---------- Kimlik doğrulama (Bölüm 7.2 / 11.5) ----------
def test_login_success(client: TestClient, test_user):
    res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == TEST_EMAIL


def test_login_never_leaks_password_hash(client: TestClient, test_user):
    """Bölüm 11.2: password_hash API yanıtında ASLA bulunmaz."""
    res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert "password_hash" not in res.text
    assert TEST_PASSWORD not in res.text


def test_login_wrong_password(client: TestClient, test_user):
    res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": "yanlis"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_user_same_error(client: TestClient, test_user):
    """Kullanıcı numaralandırma saldırısı önlenir: aynı hata kodu (Bölüm 11.5)."""
    res = client.post("/api/auth/login", json={"email": "yok@gexplatform.com", "password": "x"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_invalid_email_uses_error_envelope(client: TestClient):
    """Doğrulama hataları da standart zarf kullanır (Bölüm 7.1)."""
    res = client.post("/api/auth/login", json={"email": "bozuk", "password": "x"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_account_locks_after_max_failed_attempts(client: TestClient, test_user):
    """Bölüm 11.5: 5 başarısız denemeden sonra hesap kilitlenir."""
    for _ in range(5):
        client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": "yanlis"})
    res = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_me_requires_auth(client: TestClient):
    assert client.get("/api/auth/me").status_code == 401


def test_refresh_rejects_access_token(client: TestClient, test_user):
    login = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    access = login.json()["access_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": access})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "TOKEN_INVALID"


def test_refresh_returns_new_access_token(client: TestClient, test_user):
    login = client.post("/api/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    res = client.post("/api/auth/refresh", json={"refresh_token": login.json()["refresh_token"]})
    assert res.status_code == 200
    assert res.json()["access_token"]


# ---------- Ana Panel (Bölüm 7.3) ----------
def test_dashboard_requires_auth(client: TestClient):
    res = client.get("/api/dashboard")
    assert res.status_code == 401


def test_dashboard_returns_watchlist_data(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/dashboard", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "summary_strip" in body and "last_updated" in body
    assert body["summary_strip"][0]["symbol"] == "TST"
    assert body["summary_strip"][0]["regime"] == "negative"
    assert body["summary_strip"][0]["is_stale"] is False


# ---------- Semboller (Bölüm 7.4) ----------
def test_gex_profile_success(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/symbols/TST/gex-profile", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["symbol"] == "TST"
    assert body["gamma_flip_strike"] == 100.54
    assert len(body["strikes"]) == 3
    # Bölüm 3.11 değerleri
    net_by_strike = {s["strike"]: s["net_gex"] for s in body["strikes"]}
    assert net_by_strike[95] == -160000
    assert net_by_strike[105] == 370000


def test_symbol_not_found_returns_404(client: TestClient, auth_headers):
    res = client.get("/api/symbols/NOTAREALSTOCK/gex-profile", headers=auth_headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "SYMBOL_NOT_FOUND"


def test_gex_profile_without_data_returns_422(client: TestClient, auth_headers, db_session):
    from app.models import Symbol

    db_session.add(Symbol(ticker="EMPTY", company_name="No Data Inc."))
    db_session.commit()
    res = client.get("/api/symbols/EMPTY/gex-profile", headers=auth_headers)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "NO_OPTIONS_DATA"


def test_time_series(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/symbols/TST/time-series?range=30d", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()["series"]) == 2


def test_time_series_invalid_range(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/symbols/TST/time-series?range=999d", headers=auth_headers)
    assert res.status_code == 422


def test_symbol_search(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/symbols/search?q=test", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    assert results[0]["symbol"] == "TST"
    assert results[0]["already_in_watchlist"] is True


# ---------- İzleme listesi (Bölüm 7.5) ----------
def test_watchlist_list(client: TestClient, auth_headers, seeded_gex_data):
    res = client.get("/api/watchlist", headers=auth_headers)
    assert res.status_code == 200
    item = res.json()["items"][0]
    assert item["symbol"] == "TST"
    assert item["flip_distance"] is not None


def test_watchlist_add_duplicate_returns_409(client: TestClient, auth_headers, seeded_gex_data):
    res = client.post("/api/watchlist", json={"symbol": "TST"}, headers=auth_headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ALREADY_IN_WATCHLIST"


def test_watchlist_add_unknown_symbol_404(client: TestClient, auth_headers, test_user):
    res = client.post("/api/watchlist", json={"symbol": "NOPE"}, headers=auth_headers)
    assert res.status_code == 404


def test_watchlist_add_and_remove(client: TestClient, auth_headers, test_user, db_session):
    from app.models import Symbol

    db_session.add(Symbol(ticker="NEW", company_name="New Co."))
    db_session.commit()

    assert client.post("/api/watchlist", json={"symbol": "NEW"}, headers=auth_headers).status_code == 201
    assert client.delete("/api/watchlist/NEW", headers=auth_headers).status_code == 204
    # ikinci silme -> artık listede değil
    assert client.delete("/api/watchlist/NEW", headers=auth_headers).status_code == 404


# ---------- Veri durumu (Bölüm 7.9) ----------
def test_data_status_requires_auth(client: TestClient):
    assert client.get("/api/data-status").status_code == 401


def test_data_status_returns_sources(client: TestClient, auth_headers, db_session):
    from app.models import DataSourceStatus

    db_session.add(DataSourceStatus(source_name="opsiyon_veri_kaynagi", status="healthy"))
    db_session.commit()
    res = client.get("/api/data-status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["sources"][0]["status"] == "healthy"
