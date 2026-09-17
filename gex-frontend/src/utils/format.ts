/** Sayı/para biçimlendirme yardımcıları. */

const trNum = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 2 });

export function money(value: number, decimals = 2): string {
  return `$${value.toLocaleString("tr-TR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
}

export function pct(value: number, withSign = true): string {
  const sign = withSign && value > 0 ? "+" : "";
  return `${sign}${trNum.format(value)}%`;
}

/** Büyük GEX değerlerini kısalt: 2_100_000_000 → "2.1B$" (milyar), 45_000_000 → "45.0M$". */
export function gexShort(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B$`;
  if (abs >= 1e6) return `${sign}${(abs / 1e6).toFixed(1)}M$`;
  if (abs >= 1e3) return `${sign}${(abs / 1e3).toFixed(0)}K$`;
  return `${sign}${abs.toFixed(0)}$`;
}

export function strike(value: number): string {
  return value.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** ISO zamanı "x dk önce" gibi göster. */
export function timeAgo(iso: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "az önce";
  if (mins < 60) return `${mins} dk önce`;
  const h = Math.round(mins / 60);
  if (h < 24) return `${h} sa önce`;
  return `${Math.round(h / 24)} gün önce`;
}
