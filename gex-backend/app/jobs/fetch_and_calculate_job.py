"""Ana veri döngüsü — Build Spec Bölüm 2.4 / 8.3 / 9.2.

Akış: aktif semboller -> veri çek -> ham kaydet -> GEX hesapla -> gex_* tablolarına yaz.
Kısmi başarısızlık kuralı (Bölüm 4.5): bir sembolün hatası tüm döngüyü durdurmaz.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CalculationRun, GexByStrike, GexSummary, Symbol
from app.providers.base import MarketDataProvider
from app.services.calculation_engine import CalculationEngine, SymbolGexSummary
from app.services.data_ingestion_service import (
    fetch_symbol_data,
    persist_raw_data,
    throttle,
    to_calculation_rows,
)

logger = logging.getLogger(__name__)


def persist_gex_results(
    db: Session, symbol_id: uuid.UUID, summary: SymbolGexSummary, run_id: uuid.UUID
) -> None:
    """Hesaplanan sonuçları yazar — Bölüm 8.3.

    `gex_summary` üzerine YAZILMAZ, her döngüde yeni satır eklenir (zaman serisi, Bölüm 3.10).
    """
    db.add_all(
        GexByStrike(
            symbol_id=symbol_id,
            strike=r.strike,
            expiry=r.expiry,
            call_gex=round(r.call_gex, 2),
            put_gex=round(r.put_gex, 2),
            net_gex=round(r.net_gex, 2),
            calculation_run_id=run_id,
        )
        for r in summary.strike_results
    )
    db.add(
        GexSummary(
            symbol_id=symbol_id,
            total_net_gex=round(summary.total_net_gex, 2),
            gamma_flip_strike=summary.gamma_flip_strike,
            call_wall_strike=summary.call_wall_strike,
            put_wall_strike=summary.put_wall_strike,
            regime=summary.regime,
            spot_price_at_calc=summary.spot_price,
            calculation_run_id=run_id,
        )
    )


def fetch_and_calculate_job(
    db: Session,
    provider: MarketDataProvider,
    engine: CalculationEngine | None = None,
    tickers: list[str] | None = None,
) -> CalculationRun:
    """Tam döngüyü çalıştırır ve `calculation_runs` kaydını döndürür."""
    engine = engine or CalculationEngine()
    provider_name = provider.get_provider_name()

    run = CalculationRun(id=uuid.uuid4(), status="running")
    db.add(run)
    db.commit()

    stmt = select(Symbol).where(Symbol.is_active.is_(True))
    if tickers:
        stmt = stmt.where(Symbol.ticker.in_([t.upper() for t in tickers]))
    symbols = list(db.scalars(stmt))

    succeeded = failed = 0
    for symbol in symbols:
        try:
            price, chain = fetch_symbol_data(provider, symbol.ticker)
            if not chain:
                raise ValueError("opsiyon zinciri boş döndü")

            persist_raw_data(db, symbol, price, chain, provider_name)

            rows = to_calculation_rows(chain)
            summary = engine.calculate_symbol_gex(symbol.ticker, price.spot_price, rows)
            persist_gex_results(db, symbol.id, summary, run.id)

            db.commit()
            succeeded += 1
            logger.info(
                "%s islendi: net_gex=%.0f flip=%s rejim=%s (%d strike)",
                symbol.ticker,
                summary.total_net_gex,
                summary.gamma_flip_strike,
                summary.regime,
                len(summary.strike_results),
            )
        except Exception as e:  # noqa: BLE001 — kısmi başarısızlık (Bölüm 4.5)
            db.rollback()
            failed += 1
            logger.error("%s için işlem başarısız: %s", symbol.ticker, e)
        finally:
            throttle()

    run.finished_at = datetime.now(timezone.utc)
    run.symbols_succeeded = succeeded
    run.symbols_failed = failed
    run.status = "completed" if succeeded > 0 or not symbols else "failed"
    db.commit()

    logger.info("fetch_and_calculate_job tamamlandı: %d başarılı, %d başarısız", succeeded, failed)
    return run
