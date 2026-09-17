"""Günlük router — Build Spec Bölüm 7. İş mantığı Faz 10 ile doldurulacak."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Günlük"])


@router.get("/journal/_status", summary="Günlük modül durumu (skeleton)")
def module_status() -> dict:
    # TODO(journal): Bölüm 7'deki gerçek endpoint'lerle değiştir (Faz 10).
    return {"module": "journal", "status": "not_implemented", "phase": "Faz 10"}
