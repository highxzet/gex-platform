"""Uyarılar router — Build Spec Bölüm 7. İş mantığı Faz 10 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Uyarılar"])


@router.get("/alerts/_status", summary="Uyarılar modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(alerts): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 10).
    return {"module": "alerts", "status": "not_implemented", "phase": "Faz 10"}
