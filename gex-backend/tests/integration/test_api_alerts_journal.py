"""Uyarı / bildirim / günlük / ayar endpoint testleri — Build Spec Bölüm 13.5.

Kural: her endpoint için en az 1 başarı + 1 hata senaryosu (Bölüm 13.7).
Ayrıca Bölüm 11.6 kaynak sahipliği (403) doğrulanır.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models import Alert, JournalEntry, Notification, User


def _other_user(db: Session) -> User:
    user = User(email="baskasi@gexplatform.com", password_hash=hash_password("x" * 12))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


# ---------- Uyarılar (Bölüm 7.6) ----------
def test_create_and_list_alert(client: TestClient, auth_headers, seeded_gex_data):
    res = client.post(
        "/api/alerts",
        json={"symbol": "TST", "condition_type": "flip_distance", "threshold_value": 0.5, "channels": ["in_app"]},
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["symbol"] == "TST"

    listed = client.get("/api/alerts", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1


def test_create_alert_unknown_symbol_404(client: TestClient, auth_headers, test_user):
    res = client.post(
        "/api/alerts",
        json={"symbol": "NOPE", "condition_type": "price_level", "threshold_value": 1},
        headers=auth_headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "SYMBOL_NOT_FOUND"


def test_create_alert_invalid_condition_422(client: TestClient, auth_headers, seeded_gex_data):
    res = client.post(
        "/api/alerts",
        json={"symbol": "TST", "condition_type": "gecersiz", "threshold_value": 1},
        headers=auth_headers,
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_update_and_delete_alert(client: TestClient, auth_headers, seeded_gex_data):
    created = client.post(
        "/api/alerts",
        json={"symbol": "TST", "condition_type": "price_level", "threshold_value": 10},
        headers=auth_headers,
    ).json()

    patched = client.patch(
        f"/api/alerts/{created['id']}", json={"enabled": False, "threshold_value": 20}, headers=auth_headers
    )
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False
    assert patched.json()["threshold_value"] == 20

    assert client.delete(f"/api/alerts/{created['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/alerts/{created['id']}", headers=auth_headers).status_code == 404


def test_alert_ownership_enforced_403(client: TestClient, db_session, test_user, seeded_gex_data):
    """Bölüm 11.6: başkasının uyarısına erişilemez."""
    alert = Alert(
        user_id=test_user.id,
        symbol_id=seeded_gex_data.id,
        condition_type="price_level",
        threshold_value=1,
        channels=["in_app"],
    )
    db_session.add(alert)
    db_session.commit()

    intruder = _other_user(db_session)
    res = client.patch(f"/api/alerts/{alert.id}", json={"enabled": False}, headers=_headers_for(intruder))
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_alert_not_found_404(client: TestClient, auth_headers):
    res = client.patch(f"/api/alerts/{uuid.uuid4()}", json={"enabled": False}, headers=auth_headers)
    assert res.status_code == 404


# ---------- Bildirimler (Bölüm 7.7) ----------
def test_list_and_mark_notifications(client: TestClient, db_session, test_user, auth_headers, seeded_gex_data):
    db_session.add(
        Notification(user_id=test_user.id, message="TST: test bildirimi", related_symbol_id=seeded_gex_data.id)
    )
    db_session.commit()

    listed = client.get("/api/notifications", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()["unread_count"] == 1
    notif_id = listed.json()["items"][0]["id"]
    assert listed.json()["items"][0]["symbol"] == "TST"

    assert client.patch(f"/api/notifications/{notif_id}/read", headers=auth_headers).status_code == 204
    assert client.get("/api/notifications", headers=auth_headers).json()["unread_count"] == 0


def test_unread_only_filter(client: TestClient, db_session, test_user, auth_headers):
    db_session.add(Notification(user_id=test_user.id, message="okunmus", is_read=True))
    db_session.add(Notification(user_id=test_user.id, message="okunmamis", is_read=False))
    db_session.commit()

    res = client.get("/api/notifications?unread_only=true", headers=auth_headers)
    assert len(res.json()["items"]) == 1


def test_mark_all_read(client: TestClient, db_session, test_user, auth_headers):
    for i in range(3):
        db_session.add(Notification(user_id=test_user.id, message=f"n{i}"))
    db_session.commit()

    assert client.patch("/api/notifications/read-all", headers=auth_headers).status_code == 204
    assert client.get("/api/notifications", headers=auth_headers).json()["unread_count"] == 0


def test_notification_not_found_404(client: TestClient, auth_headers):
    res = client.patch(f"/api/notifications/{uuid.uuid4()}/read", headers=auth_headers)
    assert res.status_code == 404


# ---------- Günlük (Bölüm 7.8) ----------
def test_journal_crud(client: TestClient, auth_headers, seeded_gex_data):
    created = client.post(
        "/api/journal", json={"symbol": "TST", "content": "Flip altına düştü"}, headers=auth_headers
    )
    assert created.status_code == 201
    assert created.json()["symbol"] == "TST"
    entry_id = created.json()["id"]

    listed = client.get("/api/journal", headers=auth_headers)
    assert len(listed.json()["items"]) == 1

    filtered = client.get("/api/journal?symbol=TST", headers=auth_headers)
    assert len(filtered.json()["items"]) == 1

    patched = client.patch(f"/api/journal/{entry_id}", json={"content": "guncellendi"}, headers=auth_headers)
    assert patched.status_code == 200
    assert patched.json()["content"] == "guncellendi"

    assert client.delete(f"/api/journal/{entry_id}", headers=auth_headers).status_code == 204


def test_journal_general_note_without_symbol(client: TestClient, auth_headers, test_user):
    res = client.post("/api/journal", json={"content": "genel not"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["symbol"] is None


def test_journal_unknown_symbol_404(client: TestClient, auth_headers, test_user):
    res = client.post("/api/journal", json={"symbol": "NOPE", "content": "x"}, headers=auth_headers)
    assert res.status_code == 404


def test_journal_filter_unknown_symbol_returns_empty(client: TestClient, auth_headers, test_user):
    res = client.get("/api/journal?symbol=NOPE", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["items"] == []


def test_journal_empty_content_422(client: TestClient, auth_headers, test_user):
    res = client.post("/api/journal", json={"content": ""}, headers=auth_headers)
    assert res.status_code == 422


def test_journal_ownership_enforced_403(client: TestClient, db_session, test_user):
    entry = JournalEntry(user_id=test_user.id, content="gizli not")
    db_session.add(entry)
    db_session.commit()

    intruder = _other_user(db_session)
    res = client.delete(f"/api/journal/{entry.id}", headers=_headers_for(intruder))
    assert res.status_code == 403


# ---------- Ayarlar (Bölüm 7.10 / 17.6) ----------
def test_get_and_update_profile(client: TestClient, auth_headers, test_user):
    assert client.get("/api/settings/profile", headers=auth_headers).status_code == 200
    res = client.patch("/api/settings/profile", json={"display_name": "Yeni Ad"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["display_name"] == "Yeni Ad"


def test_update_appearance(client: TestClient, auth_headers, test_user):
    res = client.patch(
        "/api/settings/appearance", json={"theme": "light", "density": "compact"}, headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["theme_preference"] == "light"
    assert res.json()["density_preference"] == "compact"


def test_update_appearance_invalid_theme_422(client: TestClient, auth_headers, test_user):
    res = client.patch("/api/settings/appearance", json={"theme": "mor"}, headers=auth_headers)
    assert res.status_code == 422


def test_change_password_success_and_wrong_current(client: TestClient, auth_headers, test_user):
    from tests.conftest import TEST_PASSWORD

    wrong = client.post(
        "/api/settings/change-password",
        json={"current_password": "hatali", "new_password": "yenisifre123"},
        headers=auth_headers,
    )
    assert wrong.status_code == 401

    ok = client.post(
        "/api/settings/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": "yenisifre123"},
        headers=auth_headers,
    )
    assert ok.status_code == 204


def test_export_data_includes_user_content(client: TestClient, auth_headers, seeded_gex_data):
    client.post("/api/journal", json={"symbol": "TST", "content": "dışa aktarma testi"}, headers=auth_headers)
    res = client.get("/api/settings/export-data", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "TST" in body["watchlist"]
    assert any("dışa aktarma" in j["content"] for j in body["journal"])
    assert "password_hash" not in res.text


def test_delete_account_requires_confirmation(client: TestClient, auth_headers, test_user):
    bad = client.request("DELETE", "/api/settings/account?confirmation_text=HAYIR", headers=auth_headers)
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "CONFIRMATION_MISMATCH"

    ok = client.request("DELETE", "/api/settings/account?confirmation_text=SİL", headers=auth_headers)
    assert ok.status_code == 204
