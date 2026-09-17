/**
 * Mock veri katmanı — backend hazır olana kadar frontend'i tek başına çalıştırır.
 * Yapı, Build Spec Bölüm 7'deki API yanıtlarıyla birebir aynıdır; gerçek API gelince
 * yalnızca hooks içindeki kaynak değişir (mock → apiClient).
 */
import type {
  DashboardResponse,
  DataStatusResponse,
  GexProfileResponse,
  GexStrikePoint,
  Regime,
} from "@/api/types";

export interface BankRow {
  symbol: string;
  company_name: string;
  sector: string;
  spot_price: number;
  daily_change_pct: number;
  total_net_gex: number;
  gamma_flip_strike: number | null;
  call_wall_strike: number | null;
  put_wall_strike: number | null;
  regime: Regime;
  sparkline: number[];
}

export const BANKS: BankRow[] = [
  { symbol: "JPM", company_name: "JPMorgan Chase & Co.", sector: "Bankacılık", spot_price: 142.3, daily_change_pct: 0.8, total_net_gex: 2.1e9, gamma_flip_strike: 141.5, call_wall_strike: 145, put_wall_strike: 138, regime: "positive", sparkline: [1.8, 1.85, 1.92, 2.0, 2.05, 2.02, 2.1] },
  { symbol: "BAC", company_name: "Bank of America", sector: "Bankacılık", spot_price: 38.12, daily_change_pct: -0.45, total_net_gex: -0.9e9, gamma_flip_strike: 38.5, call_wall_strike: 40, put_wall_strike: 37, regime: "negative", sparkline: [-0.4, -0.5, -0.62, -0.7, -0.85, -0.88, -0.9] },
  { symbol: "WFC", company_name: "Wells Fargo & Co.", sector: "Bankacılık", spot_price: 56.4, daily_change_pct: 0.22, total_net_gex: 0.35e9, gamma_flip_strike: 56.1, call_wall_strike: 58, put_wall_strike: 54, regime: "neutral", sparkline: [0.2, 0.25, 0.3, 0.28, 0.33, 0.34, 0.35] },
  { symbol: "C", company_name: "Citigroup Inc.", sector: "Bankacılık", spot_price: 64.15, daily_change_pct: 1.1, total_net_gex: 1.2e9, gamma_flip_strike: 62.8, call_wall_strike: 66, put_wall_strike: 60, regime: "positive", sparkline: [0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2] },
  { symbol: "GS", company_name: "Goldman Sachs Group", sector: "Yatırım Bankacılığı", spot_price: 486.2, daily_change_pct: -0.3, total_net_gex: 3.4e9, gamma_flip_strike: 480, call_wall_strike: 495, put_wall_strike: 470, regime: "positive", sparkline: [3.0, 3.1, 3.2, 3.25, 3.3, 3.35, 3.4] },
  { symbol: "MS", company_name: "Morgan Stanley", sector: "Yatırım Bankacılığı", spot_price: 104.7, daily_change_pct: 0.15, total_net_gex: -0.42e9, gamma_flip_strike: 105.2, call_wall_strike: 108, put_wall_strike: 102, regime: "negative", sparkline: [-0.2, -0.25, -0.3, -0.35, -0.4, -0.41, -0.42] },
  { symbol: "USB", company_name: "U.S. Bancorp", sector: "Bankacılık", spot_price: 45.3, daily_change_pct: 0.6, total_net_gex: 0.68e9, gamma_flip_strike: 44.8, call_wall_strike: 47, put_wall_strike: 43, regime: "positive", sparkline: [0.5, 0.55, 0.6, 0.62, 0.65, 0.67, 0.68] },
  { symbol: "PNC", company_name: "PNC Financial Services", sector: "Bankacılık", spot_price: 184.9, daily_change_pct: -0.12, total_net_gex: 0.21e9, gamma_flip_strike: 184.5, call_wall_strike: 190, put_wall_strike: 178, regime: "neutral", sparkline: [0.18, 0.2, 0.19, 0.21, 0.22, 0.21, 0.21] },
];

export function findBank(symbol: string): BankRow | undefined {
  return BANKS.find((b) => b.symbol.toUpperCase() === symbol.toUpperCase());
}

/** Bir sembol için strike bazlı GEX profili üretir (flip noktası etrafında işaret değiştirir). */
export function buildStrikeProfile(bank: BankRow): GexStrikePoint[] {
  const step = bank.spot_price > 200 ? 5 : bank.spot_price > 80 ? 2.5 : 1;
  const flip = bank.gamma_flip_strike ?? bank.spot_price;
  const rows: GexStrikePoint[] = [];
  for (let k = -8; k <= 8; k++) {
    const strike = Math.round((flip + k * step) * 100) / 100;
    // flip altında negatif, üstünde pozitif; uçlara doğru sönümlü (çan benzeri)
    const dist = k;
    const magnitude = Math.exp(-(dist * dist) / 18) * bank.total_net_gex * 1.4;
    const sign = strike >= flip ? 1 : -1;
    const net = Math.round(sign * Math.abs(magnitude) * (0.6 + Math.random() * 0.5));
    const call_gex = net > 0 ? net + Math.round(Math.abs(net) * 0.25) : Math.round(Math.abs(net) * 0.2);
    const put_gex = net - call_gex;
    rows.push({ strike, net_gex: net, call_gex, put_gex });
  }
  // call/put wall'ı belirgin yap
  const cw = rows.find((r) => r.strike === bank.call_wall_strike);
  if (cw) cw.net_gex = Math.round(Math.abs(bank.total_net_gex) * 1.6);
  const pw = rows.find((r) => r.strike === bank.put_wall_strike);
  if (pw) pw.net_gex = -Math.round(Math.abs(bank.total_net_gex) * 1.3);
  return rows;
}

export const mockDashboard = (): DashboardResponse => ({
  last_updated: new Date(Date.now() - 60_000).toISOString(),
  summary_strip: BANKS.slice(0, 6).map((b, i) => ({
    symbol: b.symbol,
    company_name: b.company_name,
    spot_price: b.spot_price,
    daily_change_pct: b.daily_change_pct,
    regime: b.regime,
    data_age_minutes: 1 + i,
    is_stale: false,
  })),
  attention_items: [
    { symbol: "WFC", type: "flip_proximity", message: "Flip noktasına 0.30$ kaldı" },
    { symbol: "MS", type: "regime_change", message: "Gamma rejimi negatife döndü" },
    { symbol: "BAC", type: "gex_drop", message: "Net GEX son 24 saatte %38 düştü" },
  ],
  watchlist_preview: BANKS.slice(0, 5).map((b) => ({
    symbol: b.symbol,
    spot_price: b.spot_price,
    total_net_gex: b.total_net_gex,
    sparkline: b.sparkline,
  })),
});

export const mockGexProfile = (symbol: string): GexProfileResponse | null => {
  const bank = findBank(symbol);
  if (!bank) return null;
  return {
    symbol: bank.symbol,
    spot_price: bank.spot_price,
    gamma_flip_strike: bank.gamma_flip_strike,
    call_wall_strike: bank.call_wall_strike,
    put_wall_strike: bank.put_wall_strike,
    computed_at: new Date(Date.now() - 90_000).toISOString(),
    strikes: buildStrikeProfile(bank),
  };
};

export const mockDataStatus = (): DataStatusResponse => ({
  sources: [
    { name: "Opsiyon veri kaynağı", status: "healthy", last_success_at: new Date(Date.now() - 70_000).toISOString() },
    { name: "Fiyat veri kaynağı", status: "healthy", last_success_at: new Date(Date.now() - 50_000).toISOString() },
  ],
  recent_outages: [
    { source: "Opsiyon veri kaynağı", started_at: "2026-09-12T09:14:00Z", ended_at: "2026-09-12T09:22:00Z" },
    { source: "Fiyat veri kaynağı", started_at: "2026-09-10T16:02:00Z", ended_at: "2026-09-10T16:07:00Z" },
    { source: "Opsiyon veri kaynağı", started_at: "2026-09-08T11:40:00Z", ended_at: "2026-09-08T12:15:00Z" },
  ],
});

export interface MockAlert {
  id: string;
  symbol: string;
  condition_type: "flip_distance" | "regime_change" | "gex_pct_change" | "price_level";
  description: string;
  meta: string;
  enabled: boolean;
}

export const MOCK_ALERTS: MockAlert[] = [
  { id: "1", symbol: "JPM", condition_type: "flip_distance", description: "Flip noktasına 0.50$ kaldığında", meta: "in-app · e-posta · Aktif", enabled: true },
  { id: "2", symbol: "WFC", condition_type: "regime_change", description: "Gamma rejimi değiştiğinde", meta: "in-app · Aktif", enabled: true },
  { id: "3", symbol: "BAC", condition_type: "gex_pct_change", description: "Net GEX %25 değiştiğinde", meta: "in-app · Duraklatıldı", enabled: false },
  { id: "4", symbol: "GS", condition_type: "price_level", description: "Fiyat 495.00$ seviyesini geçtiğinde", meta: "in-app · e-posta · Aktif", enabled: true },
  { id: "5", symbol: "C", condition_type: "flip_distance", description: "Flip noktasına 1.00$ kaldığında", meta: "in-app · Aktif", enabled: true },
];

/** Deterministik pseudo-random (seed'e bağlı) — grafiklerin her render'da titrememesi için. */
function seeded(seed: number): () => number {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function hashSymbol(symbol: string): number {
  let h = 0;
  for (const ch of symbol) h = (h * 31 + ch.charCodeAt(0)) % 2147483647;
  return h + 1;
}

export interface TimeSeriesPoint {
  date: string;
  total_net_gex: number;
  spot_price: number;
}

/** Bir sembol için son N günün GEX/fiyat zaman serisi (deterministik rastgele yürüyüş). */
export function mockTimeSeries(symbol: string, days = 30): TimeSeriesPoint[] {
  const bank = findBank(symbol);
  if (!bank) return [];
  const rnd = seeded(hashSymbol(symbol));
  const pts: TimeSeriesPoint[] = [];
  let gex = bank.total_net_gex * 0.7;
  let spot = bank.spot_price * 0.96;
  const now = Date.now();
  for (let i = days - 1; i >= 0; i--) {
    gex += (bank.total_net_gex - gex) * 0.12 + (rnd() - 0.5) * Math.abs(bank.total_net_gex) * 0.18;
    spot += (bank.spot_price - spot) * 0.12 + (rnd() - 0.5) * bank.spot_price * 0.012;
    pts.push({
      date: new Date(now - i * 86400_000).toISOString().slice(0, 10),
      total_net_gex: Math.round(gex),
      spot_price: Math.round(spot * 100) / 100,
    });
  }
  return pts;
}

/** Karşılaştırma için: net GEX'i spot'a göre % strike ofsetiyle normalize edilmiş eğri. */
export function compareCurve(symbol: string): { x: number; y: number }[] {
  const bank = findBank(symbol);
  if (!bank) return [];
  const rows = buildStrikeProfile(bank);
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.net_gex)), 1);
  return rows
    .map((r) => ({ x: ((r.strike - bank.spot_price) / bank.spot_price) * 100, y: r.net_gex / maxAbs }))
    .sort((a, b) => a.x - b.x);
}

export interface JournalEntry {
  id: string;
  symbol: string | null;
  content: string;
  created_at: string;
}

export const MOCK_JOURNAL: JournalEntry[] = [
  { id: "1", symbol: "JPM", content: "Flip noktası 141.50 altına inmeye çalıştı ama call wall 145 güçlü kaldı. Pozitif gamma rejimi sürüyor, oynaklık baskılı.", created_at: new Date(Date.now() - 2 * 3600_000).toISOString() },
  { id: "2", symbol: "BAC", content: "Negatif gamma bölgesinde; put wall 37 kritik seviye. Bu seviyenin altında hızlanma beklenebilir.", created_at: new Date(Date.now() - 26 * 3600_000).toISOString() },
  { id: "3", symbol: null, content: "Genel not: bankacılık sektöründe genel olarak call-heavy yapı hâkim. GS ve JPM en yüksek pozitif net GEX'e sahip.", created_at: new Date(Date.now() - 3 * 86400_000).toISOString() },
  { id: "4", symbol: "MS", content: "Rejim negatife döndü, flip 105.20. İzleme listesine uyarı ekledim.", created_at: new Date(Date.now() - 5 * 86400_000).toISOString() },
];

export const SERIES_COLORS = ["#5b8def", "#3fb950", "#d9a441", "#f0616d", "#a78bfa", "#22d3ee"];
