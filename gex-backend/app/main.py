"""FastAPI uygulama giriş noktası.

Build Spec Bölüm 6, 14.2, 16.6. Faz 0 kabul kriteri: `/health` endpoint'i
`{"status": "healthy"}` döner.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.database import get_db
from app.routers import all_routers

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GEX Analiz Platformu API",
    version="0.1.0",
    description="Banka hisseleri için Net Gamma Exposure (GEX) hesaplama ve izleme platformu.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Global hata işleyiciler (Bölüm 14.2) ----
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Ham hata detayı ASLA yanıta konmaz (Bölüm 14.2 / 17.4) — sadece loglanır.
    logger.exception("Beklenmeyen hata: %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Bir şeyler ters gitti. Lütfen tekrar deneyin."}},
    )


# ---- Sağlık kontrolü (Bölüm 16.6) ----
@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "healthy"}


@app.get("/health/db", tags=["system"])
def health_check_db() -> dict:
    db = next(get_db())
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:  # noqa: BLE001
        return JSONResponse(  # type: ignore[return-value]
            status_code=503,
            content={"error": {"code": "DB_UNAVAILABLE", "message": "Veritabanı bağlantısı yok"}},
        )
    finally:
        db.close()


# ---- Router'ları bağla (her router boş/stub olsa da yapı hazır) ----
for router in all_routers:
    app.include_router(router, prefix="/api")
