import { Toggle } from "@/components/Toggle";
import { EmptyState, ErrorState, Skeleton } from "@/components/States";
import { useAlerts, useToggleAlert } from "@/hooks/useApi";
import { timeAgo } from "@/utils/format";
import type { ConditionType } from "@/api/types";

const CONDITION_LABEL: Record<ConditionType, (t: number) => string> = {
  flip_distance: (t) => `Flip noktasına ${t}$ kaldığında`,
  regime_change: () => "Gamma rejimi değiştiğinde",
  gex_pct_change: (t) => `Net GEX %${t} değiştiğinde`,
  price_level: (t) => `Fiyat ${t}$ seviyesini geçtiğinde`,
};

export function AlertsPage() {
  const { data, isLoading, error, refetch } = useAlerts();
  const toggle = useToggleAlert();

  return (
    <div>
      <header className="page-header dash-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Uyarılar</h1>
          <p className="page-subtitle">Koşul sağlandığında bildirim al</p>
        </div>
      </header>

      {isLoading && <Skeleton height={280} />}
      {error && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title="Henüz uyarı yok"
          hint="Uyarı oluşturma arayüzü sonraki revizyonda eklenecek; API hazır (POST /api/alerts)."
        />
      )}

      {data && data.items.length > 0 && (
        <section className="ui-card">
          <ul style={{ listStyle: "none" }}>
            {data.items.map((a) => (
              <li
                key={a.id}
                style={{
                  display: "flex", alignItems: "center", gap: "var(--space-4)",
                  padding: "var(--space-4) var(--space-5)", borderTop: "1px solid var(--color-border)",
                }}
              >
                <span className="cell-strong" style={{ minWidth: 44 }}>{a.symbol}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text)" }}>
                    {CONDITION_LABEL[a.condition_type](a.threshold_value)}
                  </div>
                  <div className="muted" style={{ fontSize: "var(--text-xs)", marginTop: 2 }}>
                    {a.channels.join(" · ")} · {a.enabled ? "Aktif" : "Duraklatıldı"}
                    {a.last_triggered_at && ` · son tetiklenme ${timeAgo(a.last_triggered_at)}`}
                  </div>
                </div>
                <Toggle
                  on={a.enabled}
                  onChange={(next) => toggle.mutate({ id: a.id, enabled: next })}
                  label={`${a.symbol} uyarısı`}
                />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
