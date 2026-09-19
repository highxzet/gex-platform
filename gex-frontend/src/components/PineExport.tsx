import { useState } from "react";
import { usePineScript } from "@/hooks/useApi";
import { ErrorState, Skeleton } from "@/components/States";
import "./pine-export.css";

interface Props {
  /** "watchlist" veya tek sembol ticker'ı */
  scope: string;
}

/**
 * GEX seviyelerini TradingView Pine indikatörü olarak dışa aktarır.
 *
 * Pine Script dışarıdan veri çekemez (sandbox, HTTP yok) — bu yüzden seviyeler
 * script'e sabit gömülür ve veri değişince yeniden üretilmesi gerekir.
 */
export function PineExport({ scope }: Props) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const { data, isLoading, error, refetch } = usePineScript(scope, open);

  async function copy() {
    if (!data) return;
    try {
      await navigator.clipboard.writeText(data.script);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* pano izni yok — kullanıcı elle seçebilir */
    }
  }

  function download() {
    if (!data) return;
    const blob = new Blob([data.script], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gex-levels-${scope}.pine`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="ui-card ui-card--pad pine-export">
      <div className="sd-card-head">
        <div>
          <h2 className="ui-card__title">TradingView Pine indikatörü</h2>
          <p className="muted" style={{ fontSize: "var(--text-xs)", marginTop: 4 }}>
            Seviyeleri kendi TradingView hesabında görmek için
          </p>
        </div>
        <button className="btn btn--ghost" onClick={() => setOpen((v) => !v)}>
          {open ? "Gizle" : "Pine kodunu üret"}
        </button>
      </div>

      {open && (
        <>
          {isLoading && <Skeleton height={200} />}
          {error && <ErrorState error={error} onRetry={() => refetch()} />}

          {data && (
            <>
              <div className="pine-meta">
                <span className="muted">
                  {data.symbols.length} sembol · {data.line_count} satır
                </span>
                {data.skipped.length > 0 && (
                  <span className="muted">
                    · veri olmayan {data.skipped.length} sembol atlandı ({data.skipped.join(", ")})
                  </span>
                )}
                <span style={{ flex: 1 }} />
                <button className="btn btn--ghost" onClick={download}>İndir (.pine)</button>
                <button className="btn btn--primary" onClick={copy}>
                  {copied ? "Kopyalandı ✓" : "Kopyala"}
                </button>
              </div>

              <ol className="pine-steps">
                <li>Kodu kopyala</li>
                <li>TradingView'de grafiği aç → alttaki <strong>Pine Editor</strong></li>
                <li>Yapıştır → <strong>Save</strong> → <strong>Add to chart</strong></li>
              </ol>

              <pre className="pine-code">{data.script}</pre>

              <p className="muted pine-warning">
                <strong>Önemli:</strong> Pine Script dışarıdan veri çekemez (TradingView sandbox'ında
                HTTP isteği yapılamaz). Seviyeler koda <strong>sabit gömülüdür</strong> — GEX verisi
                güncellendiğinde kodu yeniden üretip değiştirmen gerekir.
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}
