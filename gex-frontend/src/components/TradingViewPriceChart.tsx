import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  LineStyle,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle } from "@/api/types";

/** Grafiğe çizilecek yatay çizgi — kaynağı GEX de olabilir, Pine editörü de. */
export interface ChartLevel {
  price: number;
  label: string;
  color: string;
  /** 1..4 */
  width?: number;
  dashed?: boolean;
  dotted?: boolean;
}

interface Props {
  candles: Candle[];
  levels: ChartLevel[];
  spotPrice?: number;
  height?: number;
}

function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

/**
 * TradingView Lightweight Charts ile mum grafiği + yatay seviye çizgileri.
 *
 * Neden hazır TradingView widget'ı değil: o bir iframe'dir, üstüne kendi
 * çizgilerimizi ekleyemeyiz. Lightweight Charts açık kaynaktır ve
 * `createPriceLine()` tam olarak bunu verir (Build Spec Bölüm 2.5).
 */
export function TradingViewPriceChart({ candles, levels, spotPrice, height = 460 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

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
      rightPriceScale: {
        borderColor: cssVar("--color-border-strong", "#313a48"),
        scaleMargins: { top: 0.12, bottom: 0.12 },
      },
      timeScale: { borderColor: cssVar("--color-border-strong", "#313a48") },
      crosshair: {
        mode: 0,
        vertLine: { color: cssVar("--color-accent", "#5b8def"), labelBackgroundColor: cssVar("--color-accent", "#5b8def") },
        horzLine: { color: cssVar("--color-accent", "#5b8def"), labelBackgroundColor: cssVar("--color-accent", "#5b8def") },
      },
      localization: { locale: "tr-TR" },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: cssVar("--color-positive", "#3fb950"),
      downColor: cssVar("--color-negative", "#f0616d"),
      borderUpColor: cssVar("--color-positive", "#3fb950"),
      borderDownColor: cssVar("--color-negative", "#f0616d"),
      wickUpColor: cssVar("--color-positive", "#3fb950"),
      wickDownColor: cssVar("--color-negative", "#f0616d"),
    });

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
  }, [height]);

  // Mum verisi
  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || candles.length === 0) return;

    series.setData(
      candles.map((c) => ({
        time: (Date.parse(`${c.date}T00:00:00Z`) / 1000) as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    chart.timeScale().fitContent();
  }, [candles]);

  // Seviye çizgileri — her değişimde yeniden çizilir
  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;

    const drawn = levels.map((lv) =>
      series.createPriceLine({
        price: lv.price,
        color: lv.color,
        lineWidth: (lv.width ?? 1) as 1 | 2 | 3 | 4,
        lineStyle: lv.dotted ? LineStyle.Dotted : lv.dashed ? LineStyle.Dashed : LineStyle.Solid,
        axisLabelVisible: true,
        title: lv.label,
      })
    );

    const spot =
      spotPrice != null
        ? series.createPriceLine({
            price: spotPrice,
            color: cssVar("--color-accent", "#5b8def"),
            lineWidth: 2,
            lineStyle: LineStyle.Solid,
            axisLabelVisible: true,
            title: "Spot",
          })
        : null;

    return () => {
      drawn.forEach((l) => series.removePriceLine(l));
      if (spot) series.removePriceLine(spot);
    };
  }, [levels, spotPrice]);

  return <div ref={containerRef} style={{ width: "100%" }} />;
}
