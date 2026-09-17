"""Semboller router — Build Spec Bölüm 7. İş mantığı Faz 5 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Semboller"])


@router.get("/symbols/_status", summary="Semboller modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(symbols): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 5).
    return {"module": "symbols", "status": "not_implemented", "phase": "Faz 5"}
