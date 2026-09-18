"""GEX / panel şemaları — Build Spec Bölüm 7.3 / 7.4."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class SummaryStripItem(BaseModel):
    symbol: str
    company_name: str | None = None
    spot_price: float
    daily_change_pct: float | None = None
    regime: str
    data_age_minutes: int
    is_stale: bool


class AttentionItem(BaseModel):
    symbol: str
    type: str
    message: str


class WatchlistPreviewItem(BaseModel):
    symbol: str
    spot_price: float
    total_net_gex: float
    sparkline: list[float]


class DashboardResponse(BaseModel):
    last_updated: datetime | None
    summary_strip: list[SummaryStripItem]
    attention_items: list[AttentionItem]
    watchlist_preview: list[WatchlistPreviewItem]


class GexStrikePoint(BaseModel):
    strike: float
    net_gex: float
    call_gex: float
    put_gex: float


class GexProfileResponse(BaseModel):
    symbol: str
    spot_price: float
    gamma_flip_strike: float | None
    call_wall_strike: float | None
    put_wall_strike: float | None
    regime: str
    computed_at: datetime
    strikes: list[GexStrikePoint]


class TimeSeriesPoint(BaseModel):
    date: datetime
    total_net_gex: float
    spot_price: float


class TimeSeriesResponse(BaseModel):
    symbol: str
    series: list[TimeSeriesPoint]


class RawDataRow(BaseModel):
    strike: float
    expiry: date
    call_oi: int
    put_oi: int
    call_gamma: float | None
    put_gamma: float | None
    net_gex: float | None = None


class RawDataResponse(BaseModel):
    symbol: str
    page: int
    page_size: int
    total_rows: int
    rows: list[RawDataRow]


class CandleOut(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class LevelOut(BaseModel):
    price: float
    kind: str  # resistance | support | flip
    label: str
    strength: float
    net_gex: float


class PriceLevelsResponse(BaseModel):
    """Fiyat grafiği + GEX'ten türetilmiş destek/direnç seviyeleri."""

    symbol: str
    spot_price: float
    computed_at: datetime
    candles: list[CandleOut]
    levels: list[LevelOut]
