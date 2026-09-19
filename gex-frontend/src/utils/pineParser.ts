/**
 * Pine kodundan çizgi seviyelerini çıkarır (canlı önizleme için).
 *
 * NOT: Bu bir Pine YORUMLAYICISI DEĞİLDİR. Gerçek Pine yalnızca TradingView'in
 * sunucularında çalışır (kapalı kaynak). Burada yaptığımız şey, ürettiğimiz
 * script'in bilinen yapısından seviye atamalarını okumak — böylece kodu
 * düzenlediğinde çizgiler bizim grafiğimizde anında güncellenir.
 *
 * Desteklenen:
 *   1) Üretilen script'teki atamalar:  cw := 230   (aktif sembolün bloğunda)
 *   2) Kendi eklediğin çizgiler:       // @line 250 Hedefim #ff00ff
 *      (yorum satırı olduğu için TradingView'i bozmaz; dışa aktarırken
 *       gerçek plot() çağrısına çevrilir)
 */

export interface ParsedLevel {
  price: number;
  label: string;
  color: string;
  kind: "resistance" | "support" | "flip" | "custom";
}

/** Üretilen script'teki değişken adları → etiket ve tür. */
const KNOWN: Record<string, { label: string; kind: ParsedLevel["kind"] }> = {
  cw: { label: "Call Wall", kind: "resistance" },
  r1: { label: "1. Direnç", kind: "resistance" },
  r2: { label: "2. Direnç", kind: "resistance" },
  pw: { label: "Put Wall", kind: "support" },
  s1: { label: "1. Destek", kind: "support" },
  s2: { label: "2. Destek", kind: "support" },
  fl: { label: "Gamma Flip", kind: "flip" },
};

export const KIND_COLORS: Record<ParsedLevel["kind"], string> = {
  resistance: "#f0616d",
  support: "#3fb950",
  flip: "#d9a441",
  custom: "#5b8def",
};

/** Kod içinden verilen sembolün bloğunu ayıklar. */
function blockForSymbol(code: string, ticker: string): string {
  const lines = code.split("\n");
  const startRe = new RegExp(`syminfo\\.ticker\\s*==\\s*"${ticker}"`, "i");
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (startRe.test(lines[i])) {
      start = i;
      break;
    }
  }
  if (start === -1) return "";

  // Blok, bir sonraki if/else if satırına kadar sürer
  const out: string[] = [];
  for (let i = start + 1; i < lines.length; i++) {
    if (/^\s*(else\s+if|if)\s+syminfo\.ticker/.test(lines[i])) break;
    if (/^\s*\[/.test(lines[i])) break; // tuple dönüşü -> fonksiyon bitti
    out.push(lines[i]);
  }
  return out.join("\n");
}

/** Pine kaynağından çizilebilir seviyeleri çıkarır. */
export function parsePineLevels(code: string, ticker: string): ParsedLevel[] {
  const levels: ParsedLevel[] = [];

  // 1) Bilinen atamalar (aktif sembolün bloğu)
  const block = blockForSymbol(code, ticker);
  if (block) {
    const assign = /^\s*([a-zA-Z_]\w*)\s*:=\s*(-?\d+(?:\.\d+)?)\s*$/gm;
    let m: RegExpExecArray | null;
    while ((m = assign.exec(block)) !== null) {
      const meta = KNOWN[m[1]];
      if (!meta) continue;
      const price = Number(m[2]);
      if (!Number.isFinite(price)) continue;
      levels.push({ price, label: meta.label, color: KIND_COLORS[meta.kind], kind: meta.kind });
    }
  }

  // 2) Kullanıcının eklediği özel çizgiler:  // @line 250 Etiket #rrggbb
  const custom = /^\s*\/\/\s*@line\s+(-?\d+(?:\.\d+)?)\s*([^#\n]*?)\s*(#[0-9a-fA-F]{6})?\s*$/gm;
  let c: RegExpExecArray | null;
  while ((c = custom.exec(code)) !== null) {
    const price = Number(c[1]);
    if (!Number.isFinite(price)) continue;
    levels.push({
      price,
      label: (c[2] || "Özel").trim(),
      color: c[3] || KIND_COLORS.custom,
      kind: "custom",
    });
  }

  return levels;
}

/**
 * Dışa aktarım için: `// @line` yönergelerini gerçek Pine plot() çağrılarına çevirir.
 * Böylece TradingView'de de görünürler.
 */
export function expandPineDirectives(code: string): string {
  const customs: { price: number; label: string; color: string }[] = [];
  const re = /^\s*\/\/\s*@line\s+(-?\d+(?:\.\d+)?)\s*([^#\n]*?)\s*(#[0-9a-fA-F]{6})?\s*$/gm;
  let m: RegExpExecArray | null;
  while ((m = re.exec(code)) !== null) {
    const price = Number(m[1]);
    if (!Number.isFinite(price)) continue;
    customs.push({
      price,
      label: (m[2] || "Özel").trim(),
      color: m[3] || KIND_COLORS.custom,
    });
  }
  if (customs.length === 0) return code;

  const extra = [
    "",
    "// ── Kullanıcı tanımlı çizgiler (@line yönergelerinden üretildi) ──",
    ...customs.map(
      (c, i) =>
        `plot(${c.price}, "${c.label.replace(/"/g, "'")}", color = color.new(${c.color}, 0), ` +
        `linewidth = 1, style = plot.style_linebr)${i === 0 ? "" : ""}`
    ),
  ];
  return `${code.trimEnd()}\n${extra.join("\n")}\n`;
}
