import { useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { LineChart, type Series } from "@/components/LineChart";
import { RegimeBadge } from "@/components/RegimeBadge";
import { EmptyState, Skeleton } from "@/components/States";
import { useWatchlist } from "@/hooks/useApi";
import type { GexProfileResponse } from "@/api/types";
import { gexShort, money, strike as fmtStrike } from "@/utils/format";

const MAX = 4;
const COLORS = ["#5b8def", "#3fb950", "#d9a441", "#f0616d"];

export function ComparePage() {
  const { data: watchlist } = useWatchlist();
  const symbols = watchlist?.items.map((i) => i.symbol) ?? [];
  const [selected, setSelected] = useState<string[]>([]);

  const active = selected.length ? selected : symbols.slice(0, 3);

  const profiles = useQueries({
    queries: active.map((s) => ({
      queryKey: ["gex-profile", s],
      queryFn: () => apiClient.get<GexProfileResponse>(`/api/symbols/${s}/gex-profile`),
      staleTime: 60_000,
    })),
  });

  function toggle(sym: string) {
    setSelected((prev) => {
      const base = prev.length ? prev : symbols.slice(0, 3);
      if (base.includes(sym)) return base.filter((s) => s !== sym);
      if (base.length >= MAX) return base;
      return [...base, sym];
    });
  }

  const loading = profiles.some((p) => p.isLoading);

  /** Her sembolün eğrisi: x = spot'a göre % strike ofseti, y = normalize net GEX. */
  const series: Series[] = profiles
    .map((p, i) => {
      const d = p.data;
      if (!d || d.strikes.length === 0) return null;
      const maxAbs = Math.max(...d.strikes.map((s) => Math.abs(s.net_gex)), 1);
      return {
        name: d.symbol,
        color: COLORS[i % COLORS.length],
        points: d.strikes
          .map((s) => ({ x: ((s.strike - d.spot_price) / d.spot_price) * 100, y: s.net_gex / maxAbs }))
          .filter((pt) => Math.abs(pt.x) <= 25)
          .sort((a, b) => a.x - b.x),
      };
    })
    .filter((s): s is Series => s !== null);

  if (symbols.length === 0) {
    return (
      <div>
        <header className="page-header"><h1 className="page-title">Karşılaştır</h1></header>
        <EmptyState title="Önce izleme listenize sembol ekleyin" />
      </div>
    );
  }

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Karşılaştır</h1>
        <p className="page-subtitle">
          En fazla {MAX} sembolün GEX profil şeklini üst üste karşılaştır (spot'a göre % strike ofseti)
        </p>
      </header>

      <div className="symbol-picker" style={{ marginBottom: "var(--space-6)" }}>
        {symbols.map((s) => {
          const idx = active.indexOf(s);
          const isOn = idx >= 0;
          return (
            <button
              key={s}
              className={`symbol-chip${isOn ? " symbol-chip--active" : ""}`}
              style={isOn ? { borderColor: COLORS[idx % COLORS.length] } : undefined}
              onClick={() => toggle(s)}
            >
              {isOn && (
                <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: 999, background: COLORS[idx % COLORS.length], marginRight: 6 }} />
              )}
              {s}
            </button>
          );
        })}
      </div>

      <section className="ui-card ui-card--pad" style={{ marginBottom: "var(--space-5)" }}>
        <div className="sd-card-head">
          <h2 className="ui-card__title">Normalize Net GEX eğrisi</h2>
          <div style={{ display: "flex", gap: "var(--space-4)" }}>
            {series.map((s) => (
              <span key={s.name} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: "var(--text-xs)", color: "var(--color-text-secondary)" }}>
                <span style={{ width: 10, height: 3, background: s.color, borderRadius: 2 }} />
                {s.name}
              </span>
            ))}
          </div>
        </div>
        {loading ? (
          <Skeleton height={320} />
        ) : series.length ? (
          <LineChart series={series} height={320} zeroLine yFormat={(v) => v.toFixed(1)} xFormat={(v) => `${v > 0 ? "+" : ""}${v.toFixed(0)}%`} />
        ) : (
          <p className="muted">Karşılaştırmak için sembol seçin.</p>
        )}
      </section>

      <section className="ui-card">
        <table className="data-table">
          <thead>
            <tr><th>Sembol</th><th>Spot</th><th>Net GEX</th><th>Gamma Flip</th><th>Call Wall</th><th>Put Wall</th><th>Rejim</th></tr>
          </thead>
          <tbody>
            {active.map((sym) => {
              const item = watchlist?.items.find((i) => i.symbol === sym);
              if (!item) return null;
              return (
                <tr key={sym}>
                  <td className="cell-strong">{item.symbol}</td>
                  <td className="num">{item.spot_price != null ? money(item.spot_price) : "—"}</td>
                  <td className={`num ${(item.total_net_gex ?? 0) >= 0 ? "pos" : "neg"}`}>
                    {item.total_net_gex != null ? gexShort(item.total_net_gex) : "—"}
                  </td>
                  <td className="num">{item.gamma_flip_strike != null ? fmtStrike(item.gamma_flip_strike) : "—"}</td>
                  <td className="num pos">—</td>
                  <td className="num neg">—</td>
                  <td style={{ textAlign: "right" }}>{item.regime && <RegimeBadge regime={item.regime} compact />}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
