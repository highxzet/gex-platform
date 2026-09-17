"""Ayarlar router — Build Spec Bölüm 7. İş mantığı Faz 9 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Ayarlar"])


@router.get("/settings/_status", summary="Ayarlar modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(settings): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 9).
    return {"module": "settings", "status": "not_implemented", "phase": "Faz 9"}
