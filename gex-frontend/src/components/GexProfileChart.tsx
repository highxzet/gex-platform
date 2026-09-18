import { gexShort, strike as fmtStrike } from "@/utils/format";
import type { GexStrikePoint } from "@/api/types";

interface GexProfileChartProps {
  strikes: GexStrikePoint[];
  spotPrice: number;
  gammaFlipStrike: number | null;
  callWallStrike: number | null;
  putWallStrike: number | null;
  /** Spot çevresinde gösterilecek bant (varsayılan ±%15). */
  bandPct?: number;
  /** Bant içinde en fazla kaç strike gösterilsin (en yüksek |GEX| olanlar). */
  maxRows?: number;
}

/**
 * GEX Profili grafiği — Build Spec Bölüm 10.5 / Tasarım Bölüm 4.1.
 *
 * Gerçek zincirlerde 100+ strike olur ve derin OTM'de gamma ~ 0'dır; hepsini
 * çizmek grafiği okunamaz hale getirir. Bu yüzden spot çevresindeki anlamlı
 * bant gösterilir (endüstri araçlarının yaptığı gibi).
 */
export function GexProfileChart({
  strikes,
  spotPrice,
  gammaFlipStrike,
  callWallStrike,
  putWallStrike,
  bandPct = 0.15,
  maxRows = 28,
}: GexProfileChartProps) {
  const lo = spotPrice * (1 - bandPct);
  const hi = spotPrice * (1 + bandPct);

  // 1) spot çevresindeki bant  2) çok kalabalıksa en yüksek |GEX| olanlar
  let visible = strikes.filter((s) => s.strike >= lo && s.strike <= hi);
  if (visible.length === 0) visible = strikes;
  if (visible.length > maxRows) {
    const keep = new Set(
      [...visible].sort((a, b) => Math.abs(b.net_gex) - Math.abs(a.net_gex)).slice(0, maxRows).map((s) => s.strike)
    );
    visible = visible.filter((s) => keep.has(s.strike));
  }

  const rows = [...visible].sort((a, b) => b.strike - a.strike); // en yüksek strike üstte
  const n = rows.length;
  const hiddenCount = strikes.length - n;

  if (n === 0) return <p className="muted">Gösterilecek strike verisi yok.</p>;

  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.net_gex)), 1);

  const W = 820;
  const rowH = 24;
  const padTop = 16;
  const padBottom = 34;
  const labelW = 62;
  const rightPad = 16;
  const H = padTop + n * rowH + padBottom;
  const chartW = W - labelW - rightPad;
  const centerX = labelW + chartW / 2;
  const half = chartW / 2 - 90; // sağda etiketlere yer bırak

  const yCenter = (i: number) => padTop + i * rowH + rowH / 2;

  const priceToY = (price: number): number | null => {
    if (n < 2) return null;
    for (let i = 0; i < n - 1; i++) {
      const hiS = rows[i].strike;
      const loS = rows[i + 1].strike;
      if (price <= hiS && price >= loS) {
        const frac = (hiS - price) / (hiS - loS || 1);
        return yCenter(i) + frac * rowH;
      }
    }
    if (price > rows[0].strike) return yCenter(0);
    return yCenter(n - 1);
  };

  const barLen = (v: number) => (v / maxAbs) * half;
  const spotY = priceToY(spotPrice);
  const flipY = gammaFlipStrike != null ? priceToY(gammaFlipStrike) : null;

  return (
    <div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="GEX profili" style={{ display: "block" }}>
        <line x1={centerX} y1={padTop - 6} x2={centerX} y2={H - padBottom} stroke="var(--color-border-strong)" strokeWidth="1" />

        {rows.map((r, i) => {
          const len = barLen(r.net_gex);
          const y = yCenter(i) - 6;
          const isCallWall = callWallStrike != null && r.strike === callWallStrike;
          const isPutWall = putWallStrike != null && r.strike === putWallStrike;
          const positive = r.net_gex >= 0;
          const fill = positive ? "var(--color-positive)" : "var(--color-negative)";
          const emphasized = isCallWall || isPutWall;
          return (
            <g key={r.strike}>
              <text x={labelW - 10} y={yCenter(i) + 3} textAnchor="end" fontSize="11" fill="var(--color-text-secondary)" className="num">
                {fmtStrike(r.strike)}
              </text>
              <rect
                x={positive ? centerX : centerX + len}
                y={y}
                width={Math.max(Math.abs(len), 1)}
                height={12}
                rx={2}
                fill={fill}
                opacity={emphasized ? 0.95 : 0.65}
              />
              {emphasized && (
                <text
                  x={positive ? centerX + len + 6 : centerX + len - 6}
                  y={yCenter(i) + 3}
                  textAnchor={positive ? "start" : "end"}
                  fontSize="10"
                  fill={fill}
                  fontWeight="600"
                >
                  {isCallWall ? "Call Wall" : "Put Wall"}
                </text>
              )}
            </g>
          );
        })}

        {spotY != null && (
          <g>
            <line x1={labelW} y1={spotY} x2={W - rightPad} y2={spotY} stroke="var(--color-accent)" strokeWidth="1.25" strokeDasharray="4 3" />
            <rect x={W - rightPad - 78} y={spotY - 9} width={78} height={17} rx={3} fill="var(--color-accent)" />
            <text x={W - rightPad - 39} y={spotY + 3} textAnchor="middle" fontSize="10" fill="#fff" fontWeight="600">
              Spot {fmtStrike(spotPrice)}
            </text>
          </g>
        )}

        {flipY != null && (
          <g>
            <line x1={labelW} y1={flipY} x2={W - rightPad} y2={flipY} stroke="var(--color-warning)" strokeWidth="1" strokeDasharray="2 3" />
            <text x={labelW + 4} y={flipY - 5} fontSize="10" fill="var(--color-warning)" fontWeight="600">
              Gamma Flip {gammaFlipStrike != null ? fmtStrike(gammaFlipStrike) : ""}
            </text>
          </g>
        )}

        <text x={labelW + 4} y={H - 10} fontSize="10" fill="var(--color-text-muted)">
          ← Negatif ({gexShort(-maxAbs)})
        </text>
        <text x={W - rightPad - 4} y={H - 10} textAnchor="end" fontSize="10" fill="var(--color-text-muted)">
          Pozitif ({gexShort(maxAbs)}) →
        </text>
      </svg>

      {hiddenCount > 0 && (
        <p className="muted" style={{ fontSize: "var(--text-xs)", marginTop: "var(--space-3)" }}>
          Spot çevresindeki ±%{Math.round(bandPct * 100)} bandı gösteriliyor — {hiddenCount} uzak strike
          gizlendi (gamma'ları sıfıra yakın).
        </p>
      )}
    </div>
  );
}
