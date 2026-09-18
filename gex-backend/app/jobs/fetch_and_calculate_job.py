"""Ana veri döngüsü — Build Spec Bölüm 2.4 / 8.3 / 9.2 / 18.2.

İki mod:
  * detail=True  → ham veri + strike bazlı GEX + özet (izleme listesi sembolleri)
  * detail=False → YALNIZCA özet satırı (geniş evren taraması)

Neden iki mod: 518 sembol × ~1600 opsiyon satırı = döngü başına ~830K satır.
Bunu her taramada saklamak imkânsız (günde yüz milyonlarca satır). Geniş tarama
sembol başına 1 özet satırı yazar; detay, kullanıcının baktığı semboller için tutulur.

Kısmi başarısızlık kuralı (Bölüm 4.5): bir sembolün hatası tüm döngüyü durdurmaz.
"""
from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CalculationRun, GexByStrike, GexSummary, Symbol
from app.providers.base import MarketDataProvider
from app.services.calculation_engine import CalculationEngine, SymbolGexSummary
from app.services.data_ingestion_service import (
    fetch_symbol_data,
    persist_raw_data,
    to_calculation_rows,
)

logger = logging.getLogger(__name__)


def persist_gex_results(
    db: Session,
    symbol_id: uuid.UUID,
    summary: SymbolGexSummary,
    run_id: uuid.UUID,
    detail: bool = True,
) -> None:
    """Hesaplanan sonuçları yazar — Bölüm 8.3.

    `gex_summary` üzerine YAZILMAZ, her döngüde yeni satır eklenir (Bölüm 3.10).
    `detail=False` ise strike bazlı satırlar atlanır (evren taraması).
    """
    if detail:
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
    detail: bool = True,
    max_workers: int = 1,
) -> CalculationRun:
    """Tam döngüyü çalıştırır ve `calculation_runs` kaydını döndürür.

    Veri ÇEKME paralel yapılır (I/O-bound); veritabanına YAZMA tek thread'de
    sıralı yapılır — SQLAlchemy session'ları thread-safe değildir (Bölüm 18.2).
    """
    engine = engine or CalculationEngine()
    provider_name = provider.get_provider_name()

    run = CalculationRun(id=uuid.uuid4(), status="running")
    db.add(run)
    db.commit()

    stmt = select(Symbol).where(Symbol.is_active.is_(True))
    if tickers:
        stmt = stmt.where(Symbol.ticker.in_([t.upper() for t in tickers]))
    symbols = list(db.scalars(stmt))

    def fetch_one(symbol: Symbol):
        """Yalnızca ağ işi — DB'ye DOKUNMAZ."""
        try:
            price, chain = fetch_symbol_data(provider, symbol.ticker)
            if not chain:
                raise ValueError("opsiyon zinciri boş döndü")
            return symbol, price, chain, None
        except Exception as e:  # noqa: BLE001
            return symbol, None, None, e

    succeeded = failed = 0

    if max_workers > 1:
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(fetch_one, s) for s in symbols]
            for fut in as_completed(futures):
                results.append(fut.result())
    else:
        results = [fetch_one(s) for s in symbols]

    # --- DB yazma: TEK THREAD ---
    for symbol, price, chain, error in results:
        if error is not None:
            failed += 1
            logger.warning("%s için veri alınamadı: %s", symbol.ticker, error)
            continue
        try:
            if detail:
                persist_raw_data(db, symbol, price, chain, provider_name)

            rows = to_calculation_rows(chain)
            summary = engine.calculate_symbol_gex(symbol.ticker, price.spot_price, rows)
            persist_gex_results(db, symbol.id, summary, run.id, detail=detail)
            db.commit()
            succeeded += 1
        except Exception as e:  # noqa: BLE001
            db.rollback()
            failed += 1
            logger.error("%s için hesaplama/kayıt başarısız: %s", symbol.ticker, e)

    run.finished_at = datetime.now(timezone.utc)
    run.symbols_succeeded = succeeded
    run.symbols_failed = failed
    run.status = "completed" if succeeded > 0 or not symbols else "failed"
    db.commit()

    logger.info(
        "fetch_and_calculate_job (detail=%s, workers=%d) tamamlandı: %d başarılı, %d başarısız",
        detail, max_workers, succeeded, failed,
    )
    return run
