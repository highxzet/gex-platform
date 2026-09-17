"""Ana Panel router — Build Spec Bölüm 7. İş mantığı Faz 5 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Ana Panel"])


@router.get("/dashboard/_status", summary="Ana Panel modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(dashboard): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 5).
    return {"module": "dashboard", "status": "not_implemented", "phase": "Faz 5"}
