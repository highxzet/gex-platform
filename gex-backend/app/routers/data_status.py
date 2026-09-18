"""Veri Durumu endpoint'i — Build Spec Bölüm 7.9."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import DataSourceStatus, User
from app.schemas.watchlist import DataSourceOut, DataStatusResponse, OutageOut

router = APIRouter(tags=["Veri Durumu"])

OUTAGE_WINDOW_DAYS = 7


@router.get("/data-status", response_model=DataStatusResponse)
def get_data_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DataStatusResponse:
    # Her kaynak için en güncel durum
    latest = db.scalars(
        select(DataSourceStatus)
        .distinct(DataSourceStatus.source_name)
        .order_by(DataSourceStatus.source_name, desc(DataSourceStatus.checked_at))
    ).all()

    sources = [
        DataSourceOut(
            name=s.source_name,
            status=s.status,
            last_success_at=s.last_success_at.isoformat() if s.last_success_at else None,
        )
        for s in latest
    ]

    # Son 7 gündeki kesintiler (status != healthy olan kayıtlar)
    cutoff = datetime.now(timezone.utc) - timedelta(days=OUTAGE_WINDOW_DAYS)
    outage_rows = db.scalars(
        select(DataSourceStatus)
        .where(DataSourceStatus.checked_at >= cutoff, DataSourceStatus.status != "healthy")
        .order_by(desc(DataSourceStatus.checked_at))
        .limit(50)
    ).all()

    return DataStatusResponse(
        sources=sources,
        recent_outages=[
            OutageOut(
                source=o.source_name,
                started_at=o.checked_at.isoformat(),
                ended_at=None,
            )
            for o in outage_rows
        ],
    )
