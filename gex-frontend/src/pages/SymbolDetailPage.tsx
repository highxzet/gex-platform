import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Tabs } from "@/components/Tabs";
import { RegimeBadge } from "@/components/RegimeBadge";
import { GexProfileChart } from "@/components/GexProfileChart";
import { LineChart, type Series } from "@/components/LineChart";
import { EmptyState, ErrorState, RefreshingDot, Skeleton } from "@/components/States";
import { useGexProfile, useRawData, useTimeSeries, useWatchlist } from "@/hooks/useApi";
import { gexShort, money, strike as fmtStrike, timeAgo } from "@/utils/format";
import "./symbol-detail.css";

const TABS = [
  { value: "gex", label: "GEX Profili" },
  { value: "series", label: "Zaman Serisi" },
  { value: "raw", label: "Ham Veri" },
  { value: "notes", label: "Notlar" },
];

export function SymbolDetailPage() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState("gex");

  const { data: watchlist } = useWatchlist();
  const symbols = watchlist?.items.map((i) => i.symbol) ?? [];
  const active = (ticker ?? symbols[0] ?? "").toUpperCase();

  const { data: profile, isLoading, isFetching, error, refetch } = useGexProfile(active || undefined);
  const { data: series } = useTimeSeries(tab === "series" ? active : undefined, "30d");
  const { data: raw } = useRawData(tab === "raw" ? active : undefined, 1, 50);

  const picker = (
    <div className="symbol-picker">
      {symbols.map((s) => (
        <button
          key={s}
          className={`symbol-chip${s === active ? " symbol-chip--active" : ""}`}
          onClick={() => navigate(`/symbols/${s}`)}
        >
          {s}
        </button>
      ))}
    </div>
  );

  if (!active) {
    return (
      <div>
        <header className="page-header"><h1 className="page-title">Hisse Analizi</h1></header>
        <EmptyState title="Önce izleme listenize sembol ekleyin" />
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

  const seriesData: Series[] = series
    ? [{
        name: "Net GEX",
        color: "var(--color-accent)",
        points: series.series.map((p, i) => ({ x: i, y: p.total_net_gex })),
      }]
    : [];

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
          </div>
          <GexProfileChart
            strikes={profile.strikes}
            spotPrice={profile.spot_price}
            gammaFlipStrike={profile.gamma_flip_strike}
            callWallStrike={profile.call_wall_strike}
            putWallStrike={profile.put_wall_strike}
          />
        </section>
      )}

      {tab === "series" && (
        <section className="ui-card ui-card--pad">
          <h2 className="ui-card__title" style={{ marginBottom: "var(--space-4)" }}>Net GEX — son 30 gün</h2>
          {seriesData.length && series && series.series.length > 1 ? (
            <LineChart series={seriesData} height={300} area zeroLine yFormat={(v) => gexShort(v)} />
          ) : (
            <p className="muted">Zaman serisi için yeterli veri yok — veri toplandıkça dolacak.</p>
          )}
        </section>
      )}

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

      {tab === "notes" && (
        <section className="ui-card ui-card--pad placeholder">
          <span>Notlar Günlük sayfasından yönetiliyor.</span>
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
