"""İzleme listesi ve sembol şemaları — Build Spec Bölüm 7.4 / 7.5."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SymbolSearchItem(BaseModel):
    symbol: str
    company_name: str | None = None
    already_in_watchlist: bool = False


class SymbolSearchResponse(BaseModel):
    results: list[SymbolSearchItem]


class WatchlistItemOut(BaseModel):
    symbol: str
    company_name: str | None = None
    spot_price: float | None = None
    daily_change_pct: float | None = None
    total_net_gex: float | None = None
    gamma_flip_strike: float | None = None
    flip_distance: float | None = None
    regime: str | None = None
    sparkline: list[float] = Field(default_factory=list)


class WatchlistResponse(BaseModel):
    items: list[WatchlistItemOut]


class AddWatchlistRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)


class ReorderRequest(BaseModel):
    ordered_symbols: list[str]


class DataSourceOut(BaseModel):
    name: str
    status: str
    last_success_at: str | None = None


class OutageOut(BaseModel):
    source: str
    started_at: str
    ended_at: str | None = None


class DataStatusResponse(BaseModel):
    sources: list[DataSourceOut]
    recent_outages: list[OutageOut]
