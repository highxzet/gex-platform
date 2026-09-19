import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  LineStyle,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Candle, GexLevel } from "@/api/types";

interface Props {
  candles: Candle[];
  levels: GexLevel[];
  spotPrice: number;
  height?: number;
}

/** CSS değişkenini gerçek renge çözer (Lightweight Charts var() kabul etmez). */
function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

const KIND_COLOR_VAR: Record<string, [string, string]> = {
  resistance: ["--color-negative", "#f0616d"],
  support: ["--color-positive", "#3fb950"],
  flip: ["--color-warning", "#d9a441"],
};

/**
 * TradingView Lightweight Charts ile fiyat grafiği + GEX destek/direnç seviyeleri.
 *
 * Neden widget değil de bu: TradingView'in hazır widget'ı bir iframe'dir, üstüne
 * kendi GEX seviyelerimizi çizemeyiz. Lightweight Charts açık kaynaktır ve
 * `createPriceLine()` ile tam olarak ihtiyacımız olanı verir (Build Spec Bölüm 2.5).
 */
export function TradingViewPriceChart({ candles, levels, spotPrice, height = 460 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  // --- Grafiği bir kez kur, unmount'ta temizle ---
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
      timeScale: {
        borderColor: cssVar("--color-border-strong", "#313a48"),
      },
      crosshair: {
        mode: 0, // Normal — serbest gezinme
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

  // --- Veri ve seviyeler değiştikçe güncelle ---
  useEffect(() => {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series || candles.length === 0) return;

    series.setData(
      candles.map((c) => ({
        // "YYYY-MM-DD" -> UTC gün başlangıcı
        time: (Date.parse(`${c.date}T00:00:00Z`) / 1000) as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );

    // Önceki seviye çizgilerini temizle
    const lines = levels.map((lv) => {
      const [varName, fallback] = KIND_COLOR_VAR[lv.kind] ?? ["--color-neutral", "#8b93a1"];
      return series.createPriceLine({
        price: lv.price,
        color: cssVar(varName, fallback),
        // Çizgi kalınlığı seviyenin gücünü yansıtır
        lineWidth: (lv.kind === "flip" ? 1 : Math.max(1, Math.round(lv.strength * 3))) as 1 | 2 | 3 | 4,
        lineStyle: lv.kind === "flip" ? LineStyle.Dotted : LineStyle.Dashed,
        axisLabelVisible: true,
        title: lv.label,
      });
    });

    const spotLine = series.createPriceLine({
      price: spotPrice,
      color: cssVar("--color-accent", "#5b8def"),
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: "Spot",
    });

    chart.timeScale().fitContent();

    return () => {
      lines.forEach((l) => series.removePriceLine(l));
      series.removePriceLine(spotLine);
    };
  }, [candles, levels, spotPrice]);

  return <div ref={containerRef} style={{ width: "100%" }} />;
}
