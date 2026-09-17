interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}

/** Küçük trend çizgisi (SVG). İzleme Listesi ve Ana Panel için (Build Spec Bölüm 7.3/7.5). */
export function Sparkline({ data, width = 88, height = 28, color }: SparklineProps) {
  if (data.length < 2) return <svg width={width} height={height} />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const trendColor = color ?? (data[data.length - 1] >= data[0] ? "var(--color-positive)" : "var(--color-negative)");

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <polyline
        points={points.join(" ")}
        fill="none"
        stroke={trendColor}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
