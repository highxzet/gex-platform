import { ErrorState, Skeleton } from "@/components/States";
import { useDataStatus } from "@/hooks/useApi";
import { timeAgo } from "@/utils/format";

const STATUS_LABEL: Record<string, string> = {
  healthy: "Sağlıklı",
  degraded: "Kısmi",
  down: "Erişilemiyor",
};
const STATUS_TONE: Record<string, string> = {
  healthy: "positive",
  degraded: "neutral",
  down: "negative",
};

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleString("tr-TR", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

export function DataStatusPage() {
  const { data, isLoading, error, refetch } = useDataStatus();

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Veri Durumu</h1>
        <p className="page-subtitle">Veri kaynaklarının sağlığı ve son kesintiler</p>
      </header>

      {isLoading && <Skeleton height={100} count={2} />}
      {error && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && (
        <>
          <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-4)", marginBottom: "var(--space-6)" }}>
            {data.sources.length === 0 && (
              <div className="ui-card ui-card--pad muted">Henüz sağlık kaydı yok (healthcheck işi çalışınca dolar).</div>
            )}
            {data.sources.map((s) => (
              <div key={s.name} className="ui-card ui-card--pad" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text)", fontWeight: 500 }}>{s.name}</div>
                  <div className="muted" style={{ fontSize: "var(--text-xs)", marginTop: 4 }}>
                    Son başarı: {s.last_success_at ? timeAgo(s.last_success_at) : "—"}
                  </div>
                </div>
                <span className={`regime-badge regime-badge--${STATUS_TONE[s.status] ?? "unknown"}`}>
                  <span className="regime-badge__dot" />
                  {STATUS_LABEL[s.status] ?? s.status}
                </span>
              </div>
            ))}
          </section>

          <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "var(--space-5)" }}>
            <section className="ui-card ui-card--pad">
              <h2 className="ui-card__title" style={{ marginBottom: "var(--space-4)" }}>
                Geçmiş kesintiler (son 7 gün)
              </h2>
              {data.recent_outages.length === 0 ? (
                <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
                  Son 7 günde kesinti kaydedilmedi.
                </p>
              ) : (
                <table className="data-table">
                  <tbody>
                    {data.recent_outages.map((o, i) => (
                      <tr key={i}>
                        <td className="cell-strong">{fmtDate(o.started_at)}</td>
                        <td style={{ textAlign: "left", color: "var(--color-text-secondary)" }}>{o.source}</td>
                        <td className="num" style={{ color: "var(--color-warning)" }}>
                          {o.ended_at ? `${Math.round((+new Date(o.ended_at) - +new Date(o.started_at)) / 60000)} dk` : "sürüyor"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <aside className="ui-card ui-card--pad">
              <h2 className="ui-card__title">Yenileme sıklığı</h2>
              <p className="page-subtitle" style={{ marginTop: "var(--space-3)" }}>
                Opsiyon zinciri piyasa saatlerinde 2 dakikada bir çekilir. Piyasa kapalıyken çekim
                atlanır. Sağlık kontrolü 5 dakikada bir çalışır.
              </p>
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
