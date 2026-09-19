import { useEffect, useRef } from "react";
import {
  AreaSeries,
  LineSeries,
  LineStyle,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

export interface TvPoint {
  /** ISO tarih ("YYYY-MM-DD") veya tam ISO zaman damgası */
  time: string;
  value: number;
}

interface Props {
  points: TvPoint[];
  height?: number;
  /** Alan dolgusu (tek seri için) */
  area?: boolean;
  /** Sıfır çizgisi — Net GEX gibi işaret değiştiren seriler için */
  zeroLine?: boolean;
  color?: string;
  /** Fiyat ekseni biçimlendirici (ör. milyar $ kısaltması) */
  formatter?: (v: number) => string;
}

function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

/** TradingView Lightweight Charts ile zaman serisi (Net GEX vb.). */
export function TradingViewLineChart({
  points,
  height = 320,
  area = true,
  zeroLine = true,
  color,
  formatter,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | ISeriesApi<"Line"> | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const accent = color ?? cssVar("--color-accent", "#5b8def");

    const chart = createChart(el, {
      height,
      layout: {
        background: { color: "transparent" },
        textColor: cssVar("--color-text-secondary", "#9aa3b0"),
        fontFamily: cssVar("--font-sans", "Inter, sans-serif"),
        fontSize: 11,
      },
      grid: {
        vertLines: { color: cssVar("--color-border", "#232a35") },
        horzLines: { color: cssVar("--color-border", "#232a35") },
      },
      rightPriceScale: { borderColor: cssVar("--color-border-strong", "#313a48") },
      timeScale: { borderColor: cssVar("--color-border-strong", "#313a48") },
      crosshair: {
        mode: 0,
        vertLine: { color: accent, labelBackgroundColor: accent },
        horzLine: { color: accent, labelBackgroundColor: accent },
      },
      localization: {
        locale: "tr-TR",
        ...(formatter ? { priceFormatter: formatter } : {}),
      },
    });

    const series = area
      ? chart.addSeries(AreaSeries, {
          lineColor: accent,
          topColor: `${accent}55`,
          bottomColor: `${accent}05`,
          lineWidth: 2,
        })
      : chart.addSeries(LineSeries, { color: accent, lineWidth: 2 });

    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w) chart.applyOptions({ width: Math.floor(w) });
    });
    ro.observe(el);
    chart.applyOptions({ width: el.clientWidth });

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height, area, color, formatter]);

  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || points.length === 0) return;

    series.setData(
      points.map((p) => ({
        time: (Date.parse(p.time.length <= 10 ? `${p.time}T00:00:00Z` : p.time) / 1000) as UTCTimestamp,
        value: p.value,
      }))
    );

    const zero =
      zeroLine && points.some((p) => p.value < 0) && points.some((p) => p.value > 0)
        ? series.createPriceLine({
            price: 0,
            color: cssVar("--color-border-strong", "#313a48"),
            lineWidth: 1,
            lineStyle: LineStyle.Solid,
            axisLabelVisible: false,
            title: "",
          })
        : null;

    chart.timeScale().fitContent();

    return () => {
      if (zero) series.removePriceLine(zero);
    };
  }, [points, zeroLine]);

  return <div ref={containerRef} style={{ width: "100%" }} />;
}
