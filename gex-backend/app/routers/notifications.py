"""Bildirimler router — Build Spec Bölüm 7. İş mantığı Faz 10 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Bildirimler"])


@router.get("/notifications/_status", summary="Bildirimler modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(notifications): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 10).
    return {"module": "notifications", "status": "not_implemented", "phase": "Faz 10"}
