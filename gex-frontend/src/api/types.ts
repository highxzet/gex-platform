/**
 * Backend Pydantic şemalarına karşılık gelen TS tipleri (Build Spec Bölüm 7).
 * Skeleton: MVP endpoint'lerinin ana tipleri. Genişletme Faz 5+ ile.
 */
export type Regime = "positive" | "negative" | "neutral" | "unknown";

export interface SummaryStripItem {
  symbol: string;
  company_name: string;
  spot_price: number;
  daily_change_pct: number;
  regime: Regime;
  data_age_minutes: number;
  is_stale: boolean;
}

export interface AttentionItem {
  symbol: string;
  type: string;
  message: string;
}

export interface WatchlistPreviewItem {
  symbol: string;
  spot_price: number;
  total_net_gex: number;
  sparkline: number[];
}

export interface DashboardResponse {
  last_updated: string;
  summary_strip: SummaryStripItem[];
  attention_items: AttentionItem[];
  watchlist_preview: WatchlistPreviewItem[];
}

export interface GexStrikePoint {
  strike: number;
  net_gex: number;
  call_gex: number;
  put_gex: number;
}

export interface GexProfileResponse {
  symbol: string;
  spot_price: number;
  gamma_flip_strike: number | null;
  call_wall_strike: number | null;
  put_wall_strike: number | null;
  computed_at: string;
  strikes: GexStrikePoint[];
}

export interface DataSource {
  name: string;
  status: "healthy" | "degraded" | "down";
  last_success_at: string | null;
}

export interface DataStatusResponse {
  sources: DataSource[];
  recent_outages: {
    source: string;
    started_at: string;
    ended_at: string | null;
  }[];
}
