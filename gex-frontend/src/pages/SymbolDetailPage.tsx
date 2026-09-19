import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Tabs } from "@/components/Tabs";
import { Segment } from "@/components/Segment";
import { RegimeBadge } from "@/components/RegimeBadge";
import { GexProfileChart } from "@/components/GexProfileChart";
import { TradingViewPriceChart, type ChartLevel } from "@/components/TradingViewPriceChart";
import { TradingViewLineChart, type TvPoint } from "@/components/TradingViewLineChart";
import { SymbolSearchBox } from "@/components/SymbolSearchBox";
import { PineEditor } from "@/components/PineEditor";
import { EmptyState, ErrorState, RefreshingDot, Skeleton } from "@/components/States";
import { useGexProfile, usePriceLevels, useRawData, useTimeSeries, useWatchlist } from "@/hooks/useApi";
import { gexShort, money, strike as fmtStrike, timeAgo } from "@/utils/format";
import "./symbol-detail.css";

const TABS = [
  { value: "gex", label: "GEX Profili" },
  { value: "levels", label: "Destek / Direnç" },
  { value: "series", label: "Zaman Serisi" },
  { value: "pine", label: "Pine Editör" },
  { value: "raw", label: "Ham Veri" },
];

// Lightweight Charts CSS var() kabul etmediği için gerçek hex kullanılır.
const LEVEL_COLOR: Record<string, string> = {
  resistance: "#f0616d",
  support: "#3fb950",
  flip: "#d9a441",
};

type PriceRange = "30" | "90" | "180" | "365";
type SeriesRange = "7d" | "30d" | "90d";
type Band = "0.05" | "0.10" | "0.15" | "0.25";

export function SymbolDetailPage() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState("gex");
  const [priceRange, setPriceRange] = useState<PriceRange>("90");
  const [seriesRange, setSeriesRange] = useState<SeriesRange>("30d");
  const [band, setBand] = useState<Band>("0.15");

  const { data: watchlist } = useWatchlist();
  const quickPicks = watchlist?.items.map((i) => i.symbol) ?? [];
  const active = (ticker ?? quickPicks[0] ?? "").toUpperCase();

  const { data: profile, isLoading, isFetching, error, refetch } = useGexProfile(active || undefined);
  const { data: series } = useTimeSeries(tab === "series" ? active : undefined, seriesRange);
  const { data: raw } = useRawData(tab === "raw" ? active : undefined, 1, 50);
  const { data: priceLevels, isLoading: levelsLoading } = usePriceLevels(
    tab === "levels" ? active : undefined,
    Number(priceRange)
  );

  // GEX seviyeleri -> grafik çizgileri
  const chartLevels: ChartLevel[] = useMemo(
    () =>
      (priceLevels?.levels ?? []).map((lv) => ({
        price: lv.price,
        label: lv.label,
        color: LEVEL_COLOR[lv.kind] ?? "#8b93a1",
        width: lv.kind === "flip" ? 1 : Math.max(1, Math.round(lv.strength * 3)),
        dashed: lv.kind !== "flip",
        dotted: lv.kind === "flip",
      })),
    [priceLevels]
  );

  const seriesPoints: TvPoint[] = useMemo(
    () => (series?.series ?? []).map((p) => ({ time: p.date, value: p.total_net_gex })),
    [series]
  );

  const picker = (
    <div className="sd-picker-row">
      <SymbolSearchBox
        value={active}
        quickPicks={quickPicks}
        onSelect={(s) => navigate(`/symbols/${s}`)}
        placeholder="Sembol ara (518 sembol)…"
      />
    </div>
  );

  if (!active) {
    return (
      <div>
        <header className="page-header"><h1 className="page-title">Hisse Analizi</h1></header>
        {picker}
        <EmptyState title="Bir sembol arayın veya izleme listenize ekleyin" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div>
        {picker}
        <Skeleton height={64} />
        <div style={{ marginTop: "var(--space-6)" }}><Skeleton height={420} /></div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div>
        {picker}
        <ErrorState error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  const flipDistance =
    profile.gamma_flip_strike != null ? profile.spot_price - profile.gamma_flip_strike : null;

  return (
    <div>
      {picker}

      <header className="sd-header">
        <div>
          <div className="sd-title-row">
            <h1 className="page-title">{profile.symbol}<RefreshingDot active={isFetching} /></h1>
            <RegimeBadge regime={profile.regime} />
          </div>
          <p className="page-subtitle">Hesaplama: {timeAgo(profile.computed_at)}</p>
        </div>
        <div className="sd-price">
          <span className="sd-price__value num">{money(profile.spot_price)}</span>
          {flipDistance != null && (
            <span className={`num ${flipDistance >= 0 ? "pos" : "neg"}`}>
              Flip'e {flipDistance >= 0 ? "+" : ""}{flipDistance.toFixed(2)}$
            </span>
          )}
        </div>
      </header>

      <section className="metric-row">
        <Metric label="Gamma Flip" value={profile.gamma_flip_strike != null ? fmtStrike(profile.gamma_flip_strike) : "—"} />
        <Metric label="Call Wall" value={profile.call_wall_strike != null ? fmtStrike(profile.call_wall_strike) : "—"} tone="pos" />
        <Metric label="Put Wall" value={profile.put_wall_strike != null ? fmtStrike(profile.put_wall_strike) : "—"} tone="neg" />
        <Metric label="Strike Sayısı" value={String(profile.strikes.length)} />
      </section>

      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "gex" && (
        <section className="ui-card ui-card--pad">
          <div className="sd-card-head">
            <h2 className="ui-card__title">GEX Profili (strike bazında net gamma exposure)</h2>
            <Segment
              value={band}
              onChange={setBand}
              options={[
                { value: "0.05", label: "±%5" },
                { value: "0.10", label: "±%10" },
                { value: "0.15", label: "±%15" },
                { value: "0.25", label: "±%25" },
              ]}
            />
          </div>
          <GexProfileChart
            strikes={profile.strikes}
            spotPrice={profile.spot_price}
            gammaFlipStrike={profile.gamma_flip_strike}
            callWallStrike={profile.call_wall_strike}
            putWallStrike={profile.put_wall_strike}
            bandPct={Number(band)}
          />
          <p className="muted" style={{ fontSize: "var(--text-xs)", marginTop: "var(--space-4)" }}>
            Bu grafik strike bazlı yatay bar dağılımıdır (zaman serisi değildir), bu yüzden
            TradingView yerine kendi çizim bileşenimizi kullanır.
          </p>
        </section>
      )}

      {tab === "levels" && (
        <section className="ui-card ui-card--pad">
          <div className="sd-card-head">
            <h2 className="ui-card__title">Fiyat ve GEX destek/direnç seviyeleri</h2>
            <Segment
              value={priceRange}
              onChange={setPriceRange}
              options={[
                { value: "30", label: "1A" },
                { value: "90", label: "3A" },
                { value: "180", label: "6A" },
                { value: "365", label: "1Y" },
              ]}
            />
          </div>

          {levelsLoading && <Skeleton height={440} />}

          {priceLevels && (
            <>
              <TradingViewPriceChart
                candles={priceLevels.candles}
                levels={chartLevels}
                spotPrice={priceLevels.spot_price}
              />

              <table className="data-table" style={{ marginTop: "var(--space-5)" }}>
                <thead>
                  <tr>
                    <th>Seviye</th><th>Fiyat</th><th>Spot'a uzaklık</th><th>Güç</th><th>Net GEX</th>
                  </tr>
                </thead>
                <tbody>
                  {priceLevels.levels.map((lv, i) => {
                    const dist = ((lv.price - priceLevels.spot_price) / priceLevels.spot_price) * 100;
                    const tone = lv.kind === "resistance" ? "neg" : lv.kind === "support" ? "pos" : "";
                    return (
                      <tr key={`${lv.kind}-${lv.price}-${i}`}>
                        <td className={`cell-strong ${tone}`}>{lv.label}</td>
                        <td className="num cell-strong">{fmtStrike(lv.price)}</td>
                        <td className={`num ${dist >= 0 ? "pos" : "neg"}`}>
                          {dist >= 0 ? "+" : ""}{dist.toFixed(1)}%
                        </td>
                        <td style={{ textAlign: "right" }}>
                          <span className="strength-track">
                            <span
                              className="strength-fill"
                              style={{ width: `${Math.round(lv.strength * 100)}%`, background: LEVEL_COLOR[lv.kind] }}
                            />
                          </span>
                        </td>
                        <td className={`num ${lv.net_gex >= 0 ? "pos" : "neg"}`}>
                          {lv.net_gex ? gexShort(lv.net_gex) : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </>
          )}
        </section>
      )}

      {tab === "series" && (
        <section className="ui-card ui-card--pad">
          <div className="sd-card-head">
            <h2 className="ui-card__title">Net GEX zaman serisi</h2>
            <Segment
              value={seriesRange}
              onChange={setSeriesRange}
              options={[
                { value: "7d", label: "7G" },
                { value: "30d", label: "30G" },
                { value: "90d", label: "90G" },
              ]}
            />
          </div>
          {seriesPoints.length > 1 ? (
            <TradingViewLineChart points={seriesPoints} height={320} area zeroLine formatter={gexShort} />
          ) : (
            <p className="muted">
              Zaman serisi için en az 2 ölçüm gerekiyor ({seriesPoints.length} kayıt var) — günlük
              kapanış anlık görüntüsü işi çalıştıkça dolacak.
            </p>
          )}
        </section>
      )}

      {tab === "pine" && <PineEditor ticker={active} days={Number(priceRange)} />}

      {tab === "raw" && (
        <section className="ui-card">
          {raw ? (
            <>
              <table className="data-table">
                <thead>
                  <tr><th>Strike</th><th>Vade</th><th>Call OI</th><th>Put OI</th></tr>
                </thead>
                <tbody>
                  {raw.rows.map((r, i) => (
                    <tr key={`${r.strike}-${r.expiry}-${i}`}>
                      <td className="cell-strong num">{fmtStrike(r.strike)}</td>
                      <td className="num">{r.expiry}</td>
                      <td className="num">{r.call_oi.toLocaleString("tr-TR")}</td>
                      <td className="num">{r.put_oi.toLocaleString("tr-TR")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="muted" style={{ padding: "var(--space-3) var(--space-4)", fontSize: "var(--text-xs)" }}>
                {raw.rows.length} / {raw.total_rows.toLocaleString("tr-TR")} satır gösteriliyor
              </p>
            </>
          ) : (
            <div style={{ padding: "var(--space-5)" }}><Skeleton height={200} /></div>
          )}
        </section>
      )}
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "pos" | "neg" }) {
  return (
    <div className="ui-card ui-card--pad metric">
      <span className="ui-card__label">{label}</span>
      <span className={`metric__value num ${tone ?? ""}`}>{value}</span>
    </div>
  );
}
