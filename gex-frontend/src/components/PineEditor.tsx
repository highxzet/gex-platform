import { useEffect, useMemo, useState } from "react";
import { TradingViewPriceChart, type ChartLevel } from "@/components/TradingViewPriceChart";
import { ErrorState, Skeleton } from "@/components/States";
import { usePineScript, usePriceLevels } from "@/hooks/useApi";
import { KIND_COLORS, expandPineDirectives, parsePineLevels } from "@/utils/pineParser";
import "./pine-editor.css";

interface Props {
  ticker: string;
  days?: number;
}

/**
 * Yazılım içi Pine editörü.
 *
 * DÜRÜSTLÜK: Gerçek Pine Script yalnızca TradingView'in sunucularında çalışır
 * (kapalı kaynak, dışarıda yorumlayıcısı yok). Burada kodu ÇALIŞTIRMIYORUZ —
 * ürettiğimiz script'in bilinen yapısından seviye atamalarını okuyup grafiğe
 * çiziyoruz. Pratikte sonuç aynı: kodu düzenle, çizgiler anında güncellensin.
 */
export function PineEditor({ ticker, days = 180 }: Props) {
  const { data: pine, isLoading: pineLoading, error: pineError, refetch } = usePineScript(ticker, true);
  const { data: priceData, isLoading: priceLoading } = usePriceLevels(ticker, days);

  const [code, setCode] = useState<string>("");
  const [copied, setCopied] = useState(false);

  // Script geldiğinde editörü doldur (sembol değişince tazelenir)
  useEffect(() => {
    if (pine?.script) setCode(pine.script);
  }, [pine?.script, ticker]);

  const parsed = useMemo(() => parsePineLevels(code, ticker), [code, ticker]);

  const chartLevels: ChartLevel[] = useMemo(
    () =>
      parsed.map((lv) => ({
        price: lv.price,
        label: lv.label,
        color: lv.color,
        width: lv.kind === "custom" ? 2 : 1,
        dashed: lv.kind !== "flip",
        dotted: lv.kind === "flip",
      })),
    [parsed]
  );

  async function copy() {
    try {
      await navigator.clipboard.writeText(expandPineDirectives(code));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* pano izni yok */
    }
  }

  function download() {
    const blob = new Blob([expandPineDirectives(code)], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gex-${ticker}.pine`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function addLine() {
    const spot = priceData?.spot_price ?? 100;
    setCode((c) => `${c.trimEnd()}\n// @line ${spot.toFixed(2)} Yeni çizgi ${KIND_COLORS.custom}\n`);
  }

  if (pineLoading || priceLoading) return <Skeleton height={420} />;
  if (pineError) return <ErrorState error={pineError} onRetry={() => refetch()} />;

  return (
    <div className="pine-editor">
      <div className="pine-editor__bar">
        <div>
          <h2 className="ui-card__title">Pine Editörü</h2>
          <p className="muted" style={{ fontSize: "var(--text-xs)", marginTop: 3 }}>
            Kodu düzenle → çizgiler anında sağdaki grafikte güncellenir
          </p>
        </div>
        <span style={{ flex: 1 }} />
        <span className="pine-editor__count">{parsed.length} çizgi</span>
        <button className="btn btn--ghost" onClick={addLine}>+ Çizgi ekle</button>
        <button className="btn btn--ghost" onClick={download}>İndir</button>
        <button className="btn btn--primary" onClick={copy}>
          {copied ? "Kopyalandı ✓" : "TradingView'e kopyala"}
        </button>
      </div>

      <div className="pine-editor__split">
        <div className="pine-editor__pane">
          <textarea
            className="pine-editor__code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            spellCheck={false}
            wrap="off"
          />
        </div>

        <div className="pine-editor__pane">
          {priceData ? (
            <TradingViewPriceChart
              candles={priceData.candles}
              levels={chartLevels}
              spotPrice={priceData.spot_price}
              height={430}
            />
          ) : (
            <Skeleton height={430} />
          )}

          <ul className="pine-editor__legend">
            {parsed.map((lv, i) => (
              <li key={`${lv.label}-${i}`}>
                <span className="pine-editor__swatch" style={{ background: lv.color }} />
                <span className="pine-editor__legend-label">{lv.label}</span>
                <span className="num">{lv.price.toLocaleString("tr-TR", { minimumFractionDigits: 2 })}</span>
              </li>
            ))}
            {parsed.length === 0 && <li className="muted">Kodda çizilebilir seviye bulunamadı.</li>}
          </ul>
        </div>
      </div>

      <div className="pine-editor__help">
        <div>
          <strong>Kendi çizgini ekle:</strong> koda şu satırı yaz —{" "}
          <code>{"// @line 250 Hedefim #a78bfa"}</code>
          <br />
          Yorum satırı olduğu için TradingView'i bozmaz; dışa aktarırken gerçek{" "}
          <code>plot()</code> çağrısına çevrilir.
        </div>
        <div className="pine-editor__warn">
          <strong>Not:</strong> Pine kodu burada <strong>çalıştırılmaz</strong> — gerçek Pine sadece
          TradingView'in sunucularında çalışır. Biz seviye tanımlarını okuyup çiziyoruz. Tam
          davranış için kodu TradingView'e yapıştır.
        </div>
      </div>
    </div>
  );
}
