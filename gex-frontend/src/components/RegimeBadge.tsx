import type { Regime } from "@/api/types";

const LABELS: Record<Regime, string> = {
  positive: "Pozitif Gamma",
  negative: "Negatif Gamma",
  neutral: "Nötr",
  unknown: "Belirsiz",
};

export function RegimeBadge({ regime, compact = false }: { regime: Regime; compact?: boolean }) {
  return (
    <span className={`regime-badge regime-badge--${regime}`}>
      <span className="regime-badge__dot" />
      {compact ? LABELS[regime].split(" ")[0] : LABELS[regime]}
    </span>
  );
}
