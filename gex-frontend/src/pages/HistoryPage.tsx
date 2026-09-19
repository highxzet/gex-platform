import { useState } from "react";
import { LineChart, type Series } from "@/components/LineChart";
import { Segment } from "@/components/Segment";
import { SymbolSearchBox } from "@/components/SymbolSearchBox";
import { Tabs } from "@/components/Tabs";
import { EmptyState, ErrorState, Skeleton } from "@/components/States";
import { useLevelBacktest, useTimeSeries, useWatchlist } from "@/hooks/useApi";
import { gexShort, pct, strike as fmtPrice } from "@/utils/format";

type Range = "7d" | "30d" | "90d";

const TABS = [
  { value: "series", label: "GEX Zaman Serisi" },
  { value: "levels", label: "Seviye Analizi" },
];

const KIND_TONE: Record<string, string> = {
  resistance: "neg",
  support: "pos",
  flip: "",
};

export function HistoryPage() {
  const { data: watchlist } = useWatchlist();
  const symbols = watchlist?.items.map((i) => i.symbol) ?? [];
  const [symbol, setSymbol] = useState<string>("");
  const [range, setRange] = useState<Range>("30d");
  const [tab, setTab] = useState("levels");
  const [forwardDays, setForwardDays] = useState<"3" | "5" | "10">("5");

  const active = symbol || symbols[0] || "";
  const { data, isLoading, error, refetch } = useTimeSeries(
    tab === "series" ? active || undefined : undefined,
    range
  );
  const {
    data: bt,
    isLoading: btLoading,
    error: btError,
    refetch: btRefetch,
  } = useLevelBacktest(tab === "levels" ? active || undefined : undefined, 365, Number(forwardDays));

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
      <header className="page-header">
        <h1 className="page-title">Geçmiş / Backtest</h1>
        <p className="page-subtitle">GEX zaman serisi ve seviyelerin tarihsel isabet analizi</p>
      </header>

      <div className="sd-picker-row">
        <SymbolSearchBox value={active} quickPicks={symbols} onSelect={setSymbol} />
      </div>

      {!active && <EmptyState title="Bir sembol arayın" />}

      {active && (
        <>
          <Tabs tabs={TABS} active={tab} onChange={setTab} />

          {/* ---------- Seviye analizi ---------- */}
          {tab === "levels" && (
            <>
              <div className="ui-card ui-card--pad" style={{ marginBottom: "var(--space-5)", borderColor: "color-mix(in srgb, var(--color-warning) 35%, var(--color-border))" }}>
                <h3 className="ui-card__title" style={{ color: "var(--color-warning)" }}>
                  Bu bir GEX backtest'i değildir — dikkatle okuyun
                </h3>
                <p className="muted" style={{ fontSize: "var(--text-sm)", marginTop: "var(--space-3)", lineHeight: 1.65 }}>
                  Geçmiş opsiyon zinciri verimiz yok, bu yüzden <strong>bugünkü</strong> seviyeler geçmiş
                  fiyata uygulanıyor. Yüksek açık pozisyon, fiyatın zaten takıldığı strike'larda birikir —
                  yani seviyeler test edilen fiyat geçmişi tarafından <strong>seçilmiş</strong> olabilir
                  (döngüsellik). Sonucu kanıt değil, <strong>işaret</strong> olarak okuyun. Temiz test için
                  günlük anlık görüntüler birikiyor.
                </p>
              </div>

              <div className="sd-card-head" style={{ marginBottom: "var(--space-4)" }}>
                <span className="muted" style={{ fontSize: "var(--text-sm)" }}>
                  Dokunuştan sonra kaç gün bakılsın:
                </span>
                <Segment
                  value={forwardDays}
                  onChange={setForwardDays}
                  options={[
                    { value: "3", label: "3 gün" },
                    { value: "5", label: "5 gün" },
                    { value: "10", label: "10 gün" },
                  ]}
                />
              </div>

              {btLoading && <Skeleton height={320} />}
              {btError && <ErrorState error={btError} onRetry={() => btRefetch()} />}

              {bt && (
                <>
                  <section className="metric-row" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
                    <div className="ui-card ui-card--pad metric">
                      <span className="ui-card__label">GEX seviyeleri</span>
                      <span className="metric__value num pos">
                        {bt.gex_hold_rate != null ? `${(bt.gex_hold_rate * 100).toFixed(0)}%` : "—"}
                      </span>
                    </div>
                    <div className="ui-card ui-card--pad metric">
                      <span className="ui-card__label">Kontrol: rastgele seviye</span>
                      <span className="metric__value num muted">
                        {bt.baseline_random != null ? `${(bt.baseline_random * 100).toFixed(0)}%` : "—"}
                      </span>
                    </div>
                    <div className="ui-card ui-card--pad metric">
                      <span className="ui-card__label">Kontrol: yuvarlak sayı</span>
                      <span className="metric__value num muted">
                        {bt.baseline_round != null ? `${(bt.baseline_round * 100).toFixed(0)}%` : "—"}
                      </span>
                    </div>
                  </section>

                  <section className="ui-card ui-card--pad" style={{ marginBottom: "var(--space-5)" }}>
                    <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", lineHeight: 1.65 }}>
                      {bt.verdict}
                    </p>
                  </section>

                  <section className="ui-card">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Seviye</th><th>Fiyat</th><th>Dokunuş</th><th>Tuttu</th><th>Tutma oranı</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bt.levels.map((lv, i) => (
                          <tr key={`${lv.label}-${i}`}>
                            <td className={`cell-strong ${KIND_TONE[lv.kind] ?? ""}`}>{lv.label}</td>
                            <td className="num cell-strong">{fmtPrice(lv.price)}</td>
                            <td className="num">{lv.touches}</td>
                            <td className="num">{lv.holds}</td>
                            <td className="num">
                              {lv.hold_rate != null ? (
                                <span className={lv.hold_rate >= 0.4 ? "pos" : lv.hold_rate <= 0.25 ? "neg" : ""}>
                                  {(lv.hold_rate * 100).toFixed(0)}%
                                </span>
                              ) : (
                                <span className="muted">az dokunuş</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="muted" style={{ padding: "var(--space-3) var(--space-4)", fontSize: "var(--text-xs)" }}>
                      {bt.days} günlük fiyat geçmişi · "Tuttu" = dokunuş günü seviyenin doğru tarafında
                      kapandı ve {bt.forward_days} gün sonra hâlâ o tarafta.
                    </p>
                  </section>
                </>
              )}
            </>
          )}

          {/* ---------- GEX zaman serisi ---------- */}
          {tab === "series" && (
            <>
              <div className="sd-card-head" style={{ marginBottom: "var(--space-4)" }}>
                <span className="muted" style={{ fontSize: "var(--text-sm)" }}>Dönem:</span>
                <Segment
                  value={range}
                  onChange={setRange}
                  options={[
                    { value: "7d", label: "7G" },
                    { value: "30d", label: "30G" },
                    { value: "90d", label: "90G" },
                  ]}
                />
              </div>

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
                        Grafik için en az 2 ölçüm gerekiyor ({points.length} kayıt var). Günlük kapanış
                        anlık görüntüsü işi çalıştıkça bu seri dolacak.
                      </p>
                    )}
                  </section>
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
