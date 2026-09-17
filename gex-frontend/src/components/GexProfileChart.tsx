import { gexShort, strike as fmtStrike } from "@/utils/format";
import type { GexStrikePoint } from "@/api/types";

interface GexProfileChartProps {
  strikes: GexStrikePoint[];
  spotPrice: number;
  gammaFlipStrike: number | null;
  callWallStrike: number | null;
  putWallStrike: number | null;
}

/**
 * GEX Profili grafiği — Build Spec Bölüm 10.5 / Tasarım Bölüm 4.1.
 * Her strike için net GEX yatay bar; pozitif sağa (yeşil), negatif sola (kırmızı).
 * Spot fiyat yatay çizgi; call/put wall ve gamma flip işaretlenir.
 */
export function GexProfileChart({
  strikes,
  spotPrice,
  gammaFlipStrike,
  callWallStrike,
  putWallStrike,
}: GexProfileChartProps) {
  const rows = [...strikes].sort((a, b) => b.strike - a.strike); // en yüksek strike üstte
  const n = rows.length;
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.net_gex)), 1);

  const W = 820;
  const rowH = 26;
  const padTop = 16;
  const padBottom = 28;
  const labelW = 62;
  const rightPad = 16;
  const H = padTop + n * rowH + padBottom;
  const chartW = W - labelW - rightPad;
  const centerX = labelW + chartW / 2;
  const half = chartW / 2 - 8;

  const yCenter = (i: number) => padTop + i * rowH + rowH / 2;

  // Fiyat → y (strike aralığında doğrusal interpolasyon)
  const priceToY = (price: number): number | null => {
    if (n < 2) return null;
    for (let i = 0; i < n - 1; i++) {
      const hi = rows[i].strike;
      const lo = rows[i + 1].strike;
      if (price <= hi && price >= lo) {
        const frac = (hi - price) / (hi - lo || 1);
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
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="GEX profili" style={{ display: "block" }}>
      {/* 0 ekseni */}
      <line x1={centerX} y1={padTop - 6} x2={centerX} y2={H - padBottom} stroke="var(--color-border-strong)" strokeWidth="1" />

      {/* Barlar */}
      {rows.map((r, i) => {
        const len = barLen(r.net_gex);
        const y = yCenter(i) - 7;
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
              width={Math.abs(len)}
              height={14}
              rx={2}
              fill={fill}
              opacity={emphasized ? 0.95 : 0.6}
            />
            {emphasized && (
              <text
                x={positive ? centerX + len + 8 : centerX + len - 8}
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

      {/* Spot fiyat çizgisi */}
      {spotY != null && (
        <g>
          <line x1={labelW} y1={spotY} x2={W - rightPad} y2={spotY} stroke="var(--color-accent)" strokeWidth="1.25" strokeDasharray="4 3" />
          <rect x={W - rightPad - 70} y={spotY - 9} width={70} height={16} rx={3} fill="var(--color-accent)" />
          <text x={W - rightPad - 35} y={spotY + 2.5} textAnchor="middle" fontSize="10" fill="#fff" fontWeight="600">
            Spot {fmtStrike(spotPrice)}
          </text>
        </g>
      )}

      {/* Gamma flip çizgisi */}
      {flipY != null && (
        <g>
          <line x1={labelW} y1={flipY} x2={W - rightPad} y2={flipY} stroke="var(--color-warning)" strokeWidth="1" strokeDasharray="2 3" />
          <text x={labelW + 4} y={flipY - 4} fontSize="10" fill="var(--color-warning)" fontWeight="600">
            Gamma Flip {gammaFlipStrike != null ? fmtStrike(gammaFlipStrike) : ""}
          </text>
        </g>
      )}

      {/* Eksen etiketleri */}
      <text x={labelW + 4} y={H - 8} fontSize="10" fill="var(--color-text-muted)">
        ← Negatif GEX ({gexShort(-maxAbs)})
      </text>
      <text x={W - rightPad - 4} y={H - 8} textAnchor="end" fontSize="10" fill="var(--color-text-muted)">
        Pozitif GEX ({gexShort(maxAbs)}) →
      </text>
    </svg>
  );
}
