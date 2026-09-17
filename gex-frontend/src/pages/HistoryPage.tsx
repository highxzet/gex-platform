import { useState } from "react";
import { LineChart, type Series } from "@/components/LineChart";
import { Segment } from "@/components/Segment";
import { BANKS, mockTimeSeries } from "@/mocks/data";
import { gexShort, pct } from "@/utils/format";

type Range = "7" | "30" | "90";

export function HistoryPage() {
  const [symbol, setSymbol] = useState("JPM");
  const [range, setRange] = useState<Range>("30");

  const days = Number(range);
  const ts = mockTimeSeries(symbol, days);

  const series: Series[] = [
    { name: "Net GEX", color: "var(--color-accent)", points: ts.map((p, i) => ({ x: i, y: p.total_net_gex })) },
  ];

  const first = ts[0]?.total_net_gex ?? 0;
  const last = ts[ts.length - 1]?.total_net_gex ?? 0;
  const changePct = first !== 0 ? ((last - first) / Math.abs(first)) * 100 : 0;
  const avg = ts.reduce((s, p) => s + p.total_net_gex, 0) / (ts.length || 1);

  const tickIdx = [0, Math.floor(ts.length / 2), ts.length - 1];
  const xTickLabels = tickIdx.map((i) => ({ x: i, label: ts[i]?.date.slice(5) ?? "" }));

  return (
    <div>
      <header className="page-header dash-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Geçmiş / Backtest</h1>
          <p className="page-subtitle">Zaman içindeki toplam Net GEX değişimi</p>
        </div>
        <Segment
          value={range}
          onChange={setRange}
          options={[
            { value: "7", label: "7g" },
            { value: "30", label: "30g" },
            { value: "90", label: "90g" },
          ]}
        />
      </header>

      <div className="symbol-picker" style={{ marginBottom: "var(--space-6)" }}>
        {BANKS.map((b) => (
          <button key={b.symbol} className={`symbol-chip${b.symbol === symbol ? " symbol-chip--active" : ""}`} onClick={() => setSymbol(b.symbol)}>
            {b.symbol}
          </button>
        ))}
      </div>

      <section className="metric-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
        <div className="ui-card ui-card--pad metric">
          <span className="ui-card__label">Güncel Net GEX</span>
          <span className={`metric__value num ${last >= 0 ? "pos" : "neg"}`}>{gexShort(last)}</span>
        </div>
        <div className="ui-card ui-card--pad metric">
          <span className="ui-card__label">{days} günlük değişim</span>
          <span className={`metric__value num ${changePct >= 0 ? "pos" : "neg"}`}>{pct(changePct)}</span>
        </div>
        <div className="ui-card ui-card--pad metric">
          <span className="ui-card__label">Ortalama</span>
          <span className="metric__value num">{gexShort(avg)}</span>
        </div>
      </section>

      <section className="ui-card ui-card--pad">
        <h2 className="ui-card__title" style={{ marginBottom: "var(--space-4)" }}>{symbol} · Net GEX ({days} gün)</h2>
        <LineChart series={series} height={320} area zeroLine yFormat={(v) => gexShort(v)} xTickLabels={xTickLabels} />
      </section>
    </div>
  );
}
