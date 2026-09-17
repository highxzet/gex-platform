"""Kimlik Doğrulama router — Build Spec Bölüm 7. İş mantığı Faz 4 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Kimlik Doğrulama"])


@router.get("/auth/_status", summary="Kimlik Doğrulama modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(auth): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 4).
    return {"module": "auth", "status": "not_implemented", "phase": "Faz 4"}
