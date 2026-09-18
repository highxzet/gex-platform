import type { Candle, GexLevel } from "@/api/types";
import { strike as fmtPrice } from "@/utils/format";

interface Props {
  candles: Candle[];
  levels: GexLevel[];
  spotPrice: number;
  height?: number;
}

const KIND_COLOR: Record<string, string> = {
  resistance: "var(--color-negative)", // direnç = yukarıda satış baskısı
  support: "var(--color-positive)",
  flip: "var(--color-warning)",
};

/**
 * Fiyat mumları + GEX'ten türetilmiş destek/direnç seviyeleri.
 *
 * Yorum: spot üstünde pozitif GEX yığılması direnç (dealer yükselişte satar),
 * spot altında negatif GEX yığılması destek (dealer düşüşte alır) üretir.
 * Çizgi kalınlığı/opaklığı seviyenin gücünü (|net GEX|) yansıtır.
 */
export function PriceLevelsChart({ candles, levels, spotPrice, height = 440 }: Props) {
  if (candles.length === 0) {
    return <p className="muted">Fiyat verisi yok.</p>;
  }

  const W = 900;
  const padL = 8;
  const padR = 122; // sağda seviye etiketleri için
  const padT = 14;
  const padB = 28;
  const priceAxisW = 52;
  const chartX0 = padL + priceAxisW;
  const chartW = W - chartX0 - padR;
  const chartH = height - padT - padB;

  const lows = candles.map((c) => c.low);
  const highs = candles.map((c) => c.high);
  const levelPrices = levels.map((l) => l.price);
  let min = Math.min(...lows, ...levelPrices, spotPrice);
  let max = Math.max(...highs, ...levelPrices, spotPrice);
  const pad = (max - min) * 0.04 || 1;
  min -= pad;
  max += pad;

  const y = (p: number) => padT + (1 - (p - min) / (max - min)) * chartH;
  const slot = chartW / candles.length;
  const bodyW = Math.max(Math.min(slot * 0.62, 12), 1.5);
  const x = (i: number) => chartX0 + i * slot + slot / 2;

  const gridCount = 5;
  const gridVals = Array.from({ length: gridCount + 1 }, (_, i) => min + ((max - min) * i) / gridCount);

  // Etiketler çakışmasın diye dikey olarak ayır
  const placed: number[] = [];
  const labelY = (p: number) => {
    let ly = y(p);
    while (placed.some((v) => Math.abs(v - ly) < 13)) ly += 13;
    placed.push(ly);
    return ly;
  };

  const tickEvery = Math.max(1, Math.floor(candles.length / 6));

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${height}`} role="img" aria-label="Fiyat ve destek/direnç" style={{ display: "block" }}>
      {/* Yatay grid + fiyat ekseni */}
      {gridVals.map((gv, i) => (
        <g key={i}>
          <line x1={chartX0} y1={y(gv)} x2={chartX0 + chartW} y2={y(gv)} stroke="var(--color-border)" strokeWidth="1" />
          <text x={chartX0 - 6} y={y(gv) + 3} textAnchor="end" fontSize="10" fill="var(--color-text-muted)" className="num">
            {fmtPrice(gv)}
          </text>
        </g>
      ))}

      {/* Destek/direnç seviyeleri */}
      {levels.map((lv, i) => {
        const color = KIND_COLOR[lv.kind] ?? "var(--color-neutral)";
        const ly = y(lv.price);
        const tly = labelY(lv.price);
        const opacity = 0.35 + lv.strength * 0.55;
        return (
          <g key={`${lv.kind}-${lv.price}-${i}`}>
            <line
              x1={chartX0}
              y1={ly}
              x2={chartX0 + chartW}
              y2={ly}
              stroke={color}
              strokeWidth={lv.kind === "flip" ? 1.25 : 1 + lv.strength * 1.75}
              strokeDasharray={lv.kind === "flip" ? "2 3" : "6 4"}
              opacity={opacity}
            />
            <text x={chartX0 + chartW + 6} y={tly + 3} fontSize="10" fill={color} fontWeight="600">
              {lv.label}
            </text>
            <text x={chartX0 + chartW + 6} y={tly + 14} fontSize="9" fill="var(--color-text-muted)" className="num">
              {fmtPrice(lv.price)}
            </text>
          </g>
        );
      })}

      {/* Mumlar */}
      {candles.map((c, i) => {
        const up = c.close >= c.open;
        const color = up ? "var(--color-positive)" : "var(--color-negative)";
        const yo = y(c.open);
        const yc = y(c.close);
        const top = Math.min(yo, yc);
        const h = Math.max(Math.abs(yc - yo), 1);
        return (
          <g key={c.date}>
            <line x1={x(i)} y1={y(c.high)} x2={x(i)} y2={y(c.low)} stroke={color} strokeWidth="1" opacity={0.85} />
            <rect x={x(i) - bodyW / 2} y={top} width={bodyW} height={h} fill={color} opacity={0.9} />
          </g>
        );
      })}

      {/* Spot fiyat */}
      <g>
        <line x1={chartX0} y1={y(spotPrice)} x2={chartX0 + chartW} y2={y(spotPrice)} stroke="var(--color-accent)" strokeWidth="1.25" />
        <rect x={chartX0 + chartW - 72} y={y(spotPrice) - 9} width={70} height={17} rx={3} fill="var(--color-accent)" />
        <text x={chartX0 + chartW - 37} y={y(spotPrice) + 3} textAnchor="middle" fontSize="10" fill="#fff" fontWeight="600">
          {fmtPrice(spotPrice)}
        </text>
      </g>

      {/* Tarih ekseni */}
      {candles.map((c, i) =>
        i % tickEvery === 0 ? (
          <text key={`t-${c.date}`} x={x(i)} y={height - 8} textAnchor="middle" fontSize="9" fill="var(--color-text-muted)">
            {c.date.slice(5)}
          </text>
        ) : null
      )}
    </svg>
  );
}
