import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div style={{ display: "grid", placeItems: "center", minHeight: "100vh", textAlign: "center" }}>
      <div>
        <div style={{ fontSize: "var(--text-2xl)", fontWeight: 700 }}>404</div>
        <p style={{ color: "var(--color-text-secondary)", marginTop: "var(--space-3)" }}>
          Aradığınız sayfa bulunamadı.
        </p>
        <Link
          to="/"
          style={{
            display: "inline-block",
            marginTop: "var(--space-5)",
            color: "var(--color-accent)",
            fontSize: "var(--text-sm)",
          }}
        >
          ← Ana Panel'e dön
        </Link>
      </div>
    </div>
  );
}
