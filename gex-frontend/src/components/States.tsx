import type { ReactNode } from "react";
import { ApiError } from "@/api/client";
import { messageForCode } from "@/utils/errorMessages";

/** İskelet yükleyici — ilk yükleme için (tasarım Bölüm 7.1 "Yükleniyor"). */
export function Skeleton({ height = 80, count = 1 }: { height?: number; count?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height, borderRadius: "var(--radius-lg)" }}
          aria-hidden
        />
      ))}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message =
    error instanceof ApiError
      ? messageForCode(error.code, error.message)
      : "Sunucuya ulaşılamadı. Backend çalışıyor mu?";

  return (
    <div className="ui-card ui-card--pad state-block">
      <span className="state-block__title">Veri alınamadı</span>
      <span className="muted">{message}</span>
      {onRetry && (
        <button className="btn btn--ghost" style={{ marginTop: "var(--space-3)" }} onClick={onRetry}>
          Tekrar dene
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <div className="ui-card ui-card--pad state-block">
      <span className="state-block__title">{title}</span>
      {hint && <span className="muted">{hint}</span>}
    </div>
  );
}

/** Arka plan yenilemesi göstergesi (isFetching && !isLoading). */
export function RefreshingDot({ active }: { active: boolean }) {
  if (!active) return null;
  return <span className="refreshing-dot" title="Yenileniyor" />;
}
