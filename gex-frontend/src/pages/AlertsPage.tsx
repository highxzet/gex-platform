import { useState } from "react";
import { Toggle } from "@/components/Toggle";
import { MOCK_ALERTS, type MockAlert } from "@/mocks/data";

export function AlertsPage() {
  const [alerts, setAlerts] = useState<MockAlert[]>(MOCK_ALERTS);

  const toggle = (id: string) =>
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, enabled: !a.enabled } : a)));

  return (
    <div>
      <header className="page-header dash-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">Uyarılar</h1>
          <p className="page-subtitle">Koşul sağlandığında bildirim al</p>
        </div>
        <button className="btn btn--primary">+ Yeni uyarı</button>
      </header>

      <section className="ui-card">
        <ul style={{ listStyle: "none" }}>
          {alerts.map((a) => (
            <li
              key={a.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-4)",
                padding: "var(--space-4) var(--space-5)",
                borderTop: "1px solid var(--color-border)",
              }}
            >
              <span className="cell-strong" style={{ minWidth: 44 }}>{a.symbol}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text)" }}>{a.description}</div>
                <div className="muted" style={{ fontSize: "var(--text-xs)", marginTop: 2 }}>{a.meta}</div>
              </div>
              <Toggle on={a.enabled} onChange={() => toggle(a.id)} label={`${a.symbol} uyarısı`} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
