"""Veri Durumu router — Build Spec Bölüm 7. İş mantığı Faz 5 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Veri Durumu"])


@router.get("/data_status/_status", summary="Veri Durumu modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(data_status): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 5).
    return {"module": "data_status", "status": "not_implemented", "phase": "Faz 5"}
