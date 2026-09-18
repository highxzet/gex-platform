import { useState } from "react";
import { LineChart, type Series } from "@/components/LineChart";
import { Segment } from "@/components/Segment";
import { SymbolSearchBox } from "@/components/SymbolSearchBox";
import { EmptyState, ErrorState, Skeleton } from "@/components/States";
import { useTimeSeries, useWatchlist } from "@/hooks/useApi";
import { gexShort, pct } from "@/utils/format";

type Range = "7d" | "30d" | "90d";

export function HistoryPage() {
  const { data: watchlist } = useWatchlist();
  const symbols = watchlist?.items.map((i) => i.symbol) ?? [];
  const [symbol, setSymbol] = useState<string>("");
  const [range, setRange] = useState<Range>("30d");

  const active = symbol || symbols[0] || "";
  const { data, isLoading, error, refetch } = useTimeSeries(active || undefined, range);

  const points = data?.series ?? [];
  const first = points[0]?.total_net_gex ?? 0;
  const last = points[points.length - 1]?.total_net_gex ?? 0;
  const changePct = first !== 0 ? ((last - first) / Math.abs(first)) * 100 : 0;
  const avg = points.length ? points.reduce((s, p) => s + p.total_net_gex, 0) / points.length : 0;

  const series: Series[] = [
    { name: "Net GEX", color: "var(--color-accent)", points: points.map((p, i) => ({ x: i, y: p.total_net_gex })) },
  ];
  const tickIdx = points.length ? [0, Math.floor(points.length / 2), points.length - 1] : [];
  const xTickLabels = tickIdx.map((i) => ({ x: i, label: points[i]?.date.slice(5, 10) ?? "" }));

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
            { value: "7d", label: "7g" },
            { value: "30d", label: "30g" },
            { value: "90d", label: "90g" },
          ]}
        />
      </header>

      <div className="sd-picker-row">
        <SymbolSearchBox value={active} quickPicks={symbols} onSelect={setSymbol} />
      </div>

      {!active && <EmptyState title="Önce izleme listenize sembol ekleyin" />}
      {isLoading && <Skeleton height={320} />}
      {error && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && (
        <>
          <section className="metric-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            <div className="ui-card ui-card--pad metric">
              <span className="ui-card__label">Güncel Net GEX</span>
              <span className={`metric__value num ${last >= 0 ? "pos" : "neg"}`}>{gexShort(last)}</span>
            </div>
            <div className="ui-card ui-card--pad metric">
              <span className="ui-card__label">Dönem değişimi</span>
              <span className={`metric__value num ${changePct >= 0 ? "pos" : "neg"}`}>
                {points.length > 1 ? pct(changePct) : "—"}
              </span>
            </div>
            <div className="ui-card ui-card--pad metric">
              <span className="ui-card__label">Ortalama</span>
              <span className="metric__value num">{gexShort(avg)}</span>
            </div>
          </section>

          <section className="ui-card ui-card--pad">
            <h2 className="ui-card__title" style={{ marginBottom: "var(--space-4)" }}>
              {active} · Net GEX ({range})
            </h2>
            {points.length > 1 ? (
              <LineChart series={series} height={320} area zeroLine yFormat={(v) => gexShort(v)} xTickLabels={xTickLabels} />
            ) : (
              <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
                Grafik için en az 2 ölçüm gerekiyor. Şu an {points.length} kayıt var — veri toplama işi
                çalıştıkça (2 dakikada bir) grafik dolacak.
              </p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
