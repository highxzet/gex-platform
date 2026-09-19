/**
 * Backend Pydantic şemalarına karşılık gelen TS tipleri (Build Spec Bölüm 7).
 * Bu dosya backend `app/schemas/*.py` ile BİRE BİR uyumlu tutulmalıdır.
 */
export type Regime = "positive" | "negative" | "neutral" | "unknown";

// ---------- Auth (Bölüm 7.2) ----------
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  theme_preference: "dark" | "light" | "system";
  density_preference: "standard" | "compact";
  onboarding_completed: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// ---------- Ana Panel (Bölüm 7.3) ----------
export interface SummaryStripItem {
  symbol: string;
  company_name: string | null;
  spot_price: number;
  daily_change_pct: number | null;
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
  last_updated: string | null;
  summary_strip: SummaryStripItem[];
  attention_items: AttentionItem[];
  watchlist_preview: WatchlistPreviewItem[];
}

// ---------- Semboller (Bölüm 7.4) ----------
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
  regime: Regime;
  computed_at: string;
  strikes: GexStrikePoint[];
}

export interface TimeSeriesPoint {
  date: string;
  total_net_gex: number;
  spot_price: number;
}

export interface TimeSeriesResponse {
  symbol: string;
  series: TimeSeriesPoint[];
}

export interface RawDataRow {
  strike: number;
  expiry: string;
  call_oi: number;
  put_oi: number;
  call_gamma: number | null;
  put_gamma: number | null;
  net_gex: number | null;
}

export interface RawDataResponse {
  symbol: string;
  page: number;
  page_size: number;
  total_rows: number;
  rows: RawDataRow[];
}

export interface SymbolSearchItem {
  symbol: string;
  company_name: string | null;
  already_in_watchlist: boolean;
}

export interface SymbolSearchResponse {
  results: SymbolSearchItem[];
}

// ---------- İzleme Listesi (Bölüm 7.5) ----------
export interface WatchlistItem {
  symbol: string;
  company_name: string | null;
  spot_price: number | null;
  daily_change_pct: number | null;
  total_net_gex: number | null;
  gamma_flip_strike: number | null;
  flip_distance: number | null;
  regime: Regime | null;
  sparkline: number[];
}

export interface WatchlistResponse {
  items: WatchlistItem[];
}

// ---------- Uyarılar (Bölüm 7.6) ----------
export type ConditionType = "flip_distance" | "regime_change" | "gex_pct_change" | "price_level";

export interface Alert {
  id: string;
  symbol: string;
  condition_type: ConditionType;
  threshold_value: number;
  channels: string[];
  enabled: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

export interface AlertListResponse {
  items: Alert[];
}

// ---------- Bildirimler (Bölüm 7.7) ----------
export interface Notification {
  id: string;
  message: string;
  symbol: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  unread_count: number;
}

// ---------- Günlük (Bölüm 7.8) ----------
export interface JournalEntry {
  id: string;
  symbol: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface JournalListResponse {
  items: JournalEntry[];
}

// ---------- Veri Durumu (Bölüm 7.9) ----------
export interface DataSource {
  name: string;
  status: "healthy" | "degraded" | "down";
  last_success_at: string | null;
}

export interface Outage {
  source: string;
  started_at: string;
  ended_at: string | null;
}

export interface DataStatusResponse {
  sources: DataSource[];
  recent_outages: Outage[];
}

// ---------- Fiyat + Destek/Direnç ----------
export interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type LevelKind = "resistance" | "support" | "flip";

export interface GexLevel {
  price: number;
  kind: LevelKind;
  label: string;
  strength: number;
  net_gex: number;
}

export interface PriceLevelsResponse {
  symbol: string;
  spot_price: number;
  computed_at: string;
  candles: Candle[];
  levels: GexLevel[];
}

// ---------- Seviye analizi (edge doğrulama) ----------
export interface LevelStat {
  label: string;
  kind: LevelKind;
  price: number;
  touches: number;
  holds: number;
  hold_rate: number | null;
}

export interface LevelBacktestResponse {
  symbol: string;
  days: number;
  forward_days: number;
  levels: LevelStat[];
  baseline_random: number | null;
  baseline_round: number | null;
  gex_hold_rate: number | null;
  verdict: string;
}
