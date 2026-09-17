"""İzleme Listesi router — Build Spec Bölüm 7. İş mantığı Faz 5 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["İzleme Listesi"])


@router.get("/watchlist/_status", summary="İzleme Listesi modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(watchlist): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 5).
    return {"module": "watchlist", "status": "not_implemented", "phase": "Faz 5"}
