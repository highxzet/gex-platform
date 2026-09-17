export interface Series {
  name: string;
  color: string;
  points: { x: number; y: number }[];
}

interface LineChartProps {
  series: Series[];
  height?: number;
  yFormat?: (v: number) => string;
  xFormat?: (v: number) => string;
  xTickLabels?: { x: number; label: string }[];
  area?: boolean;
  zeroLine?: boolean;
}

/** Genel amaçlı çok-serili çizgi grafiği (saf SVG). Karşılaştır ve Geçmiş için. */
export function LineChart({
  series,
  height = 300,
  yFormat = (v) => `${v}`,
  xFormat,
  xTickLabels,
  area = false,
  zeroLine = false,
}: LineChartProps) {
  const W = 840;
  const padL = 60;
  const padR = 16;
  const padT = 14;
  const padB = 28;
  const chartW = W - padL - padR;
  const chartH = height - padT - padB;

  const allPts = series.flatMap((s) => s.points);
  if (allPts.length === 0) return <svg width="100%" viewBox={`0 0 ${W} ${height}`} />;

  const xs = allPts.map((p) => p.x);
  const ys = allPts.map((p) => p.y);
  let yMin = Math.min(...ys, zeroLine ? 0 : Math.min(...ys));
  let yMax = Math.max(...ys, zeroLine ? 0 : Math.max(...ys));
  if (yMin === yMax) { yMin -= 1; yMax += 1; }
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs) || 1;

  const sx = (x: number) => padL + ((x - xMin) / (xMax - xMin || 1)) * chartW;
  const sy = (y: number) => padT + (1 - (y - yMin) / (yMax - yMin || 1)) * chartH;

  const yTicks = 4;
  const gridY = Array.from({ length: yTicks + 1 }, (_, i) => yMin + ((yMax - yMin) * i) / yTicks);

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${height}`} role="img" style={{ display: "block" }}>
      {/* yatay grid + y etiketleri */}
      {gridY.map((gy, i) => (
        <g key={i}>
          <line x1={padL} y1={sy(gy)} x2={W - padR} y2={sy(gy)} stroke="var(--color-border)" strokeWidth="1" />
          <text x={padL - 8} y={sy(gy) + 3} textAnchor="end" fontSize="10" fill="var(--color-text-muted)" className="num">
            {yFormat(gy)}
          </text>
        </g>
      ))}

      {/* sıfır çizgisi */}
      {zeroLine && yMin < 0 && yMax > 0 && (
        <line x1={padL} y1={sy(0)} x2={W - padR} y2={sy(0)} stroke="var(--color-border-strong)" strokeWidth="1.25" />
      )}

      {/* x etiketleri */}
      {(xTickLabels ?? []).map((t, i) => (
        <text key={i} x={sx(t.x)} y={height - 8} textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">
          {t.label}
        </text>
      ))}
      {!xTickLabels && xFormat && (
        <>
          <text x={padL} y={height - 8} textAnchor="start" fontSize="10" fill="var(--color-text-muted)">{xFormat(xMin)}</text>
          <text x={W - padR} y={height - 8} textAnchor="end" fontSize="10" fill="var(--color-text-muted)">{xFormat(xMax)}</text>
        </>
      )}

      {/* seriler */}
      {series.map((s) => {
        const pts = s.points.map((p) => `${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(" ");
        const areaPath =
          area && series.length === 1
            ? `M ${sx(s.points[0].x)},${sy(Math.max(yMin, 0))} L ` +
              s.points.map((p) => `${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join(" L ") +
              ` L ${sx(s.points[s.points.length - 1].x)},${sy(Math.max(yMin, 0))} Z`
            : null;
        return (
          <g key={s.name}>
            {areaPath && <path d={areaPath} fill={s.color} opacity={0.12} />}
            <polyline points={pts} fill="none" stroke={s.color} strokeWidth="1.75" strokeLinejoin="round" strokeLinecap="round" />
          </g>
        );
      })}
    </svg>
  );
}
