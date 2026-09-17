import { useState } from "react";
import { LineChart, type Series } from "@/components/LineChart";
import { RegimeBadge } from "@/components/RegimeBadge";
import { BANKS, compareCurve, findBank, SERIES_COLORS } from "@/mocks/data";
import { gexShort, money, strike as fmtStrike } from "@/utils/format";

const MAX = 4;

export function ComparePage() {
  const [selected, setSelected] = useState<string[]>(["JPM", "BAC", "C"]);

  function toggle(sym: string) {
    setSelected((prev) => {
      if (prev.includes(sym)) return prev.filter((s) => s !== sym);
      if (prev.length >= MAX) return prev;
      return [...prev, sym];
    });
  }

  const series: Series[] = selected.map((sym, i) => ({
    name: sym,
    color: SERIES_COLORS[i % SERIES_COLORS.length],
    points: compareCurve(sym),
  }));

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Karşılaştır</h1>
        <p className="page-subtitle">En fazla {MAX} sembolün GEX profil şeklini üst üste karşılaştır (spot'a göre % strike ofseti)</p>
      </header>

      {/* Sembol seçici */}
      <div className="symbol-picker" style={{ marginBottom: "var(--space-6)" }}>
        {BANKS.map((b) => {
          const idx = selected.indexOf(b.symbol);
          const active = idx >= 0;
          return (
            <button
              key={b.symbol}
              className={`symbol-chip${active ? " symbol-chip--active" : ""}`}
              style={active ? { borderColor: SERIES_COLORS[idx % SERIES_COLORS.length], color: "var(--color-text)" } : undefined}
              onClick={() => toggle(b.symbol)}
            >
              {active && (
                <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: 999, background: SERIES_COLORS[idx % SERIES_COLORS.length], marginRight: 6 }} />
              )}
              {b.symbol}
            </button>
          );
        })}
      </div>

      {/* Grafik */}
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
        {series.length > 0 ? (
          <LineChart series={series} height={320} zeroLine yFormat={(v) => v.toFixed(1)} xFormat={(v) => `${v > 0 ? "+" : ""}${v.toFixed(0)}%`} />
        ) : (
          <p className="muted">Karşılaştırmak için en az bir sembol seçin.</p>
        )}
      </section>

      {/* Karşılaştırma tablosu */}
      <section className="ui-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Sembol</th>
              <th>Spot</th>
              <th>Net GEX</th>
              <th>Gamma Flip</th>
              <th>Call Wall</th>
              <th>Put Wall</th>
              <th>Rejim</th>
            </tr>
          </thead>
          <tbody>
            {selected.map((sym) => {
              const b = findBank(sym)!;
              return (
                <tr key={sym}>
                  <td className="cell-strong">{b.symbol}</td>
                  <td className="num">{money(b.spot_price)}</td>
                  <td className={`num ${b.total_net_gex >= 0 ? "pos" : "neg"}`}>{gexShort(b.total_net_gex)}</td>
                  <td className="num">{b.gamma_flip_strike != null ? fmtStrike(b.gamma_flip_strike) : "—"}</td>
                  <td className="num pos">{b.call_wall_strike != null ? fmtStrike(b.call_wall_strike) : "—"}</td>
                  <td className="num neg">{b.put_wall_strike != null ? fmtStrike(b.put_wall_strike) : "—"}</td>
                  <td style={{ textAlign: "right" }}><RegimeBadge regime={b.regime} compact /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
