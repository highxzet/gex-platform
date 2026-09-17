/** Veri tazeliği kategorisi — Build Spec Bölüm 10.3. */
export type FreshnessCategory = "fresh" | "aging" | "old" | "stale";

export function getDataAgeCategory(timestamp: string): FreshnessCategory {
  const ageMinutes = (Date.now() - new Date(timestamp).getTime()) / 60_000;
  if (ageMinutes <= 2) return "fresh";
  if (ageMinutes <= 15) return "aging";
  if (ageMinutes <= 60) return "old";
  return "stale";
}

export function freshnessColor(category: FreshnessCategory): string {
  switch (category) {
    case "fresh":
      return "var(--color-positive)";
    case "aging":
      return "var(--color-accent)";
    case "old":
      return "var(--color-warning)";
    case "stale":
      return "var(--color-negative)";
  }
}
