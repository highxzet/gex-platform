import type { ReactNode } from "react";

interface PageProps {
  title: string;
  tag?: string;
  subtitle?: string;
  specRef?: string;
  children?: ReactNode;
}

/** Ortak sayfa iskeleti — başlık + isteğe bağlı içerik. Faz 5+ ile gerçek içerik gelir. */
export function Page({ title, tag, subtitle, specRef, children }: PageProps) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">
          {title}
          {tag && <span className="page-tag">{tag}</span>}
        </h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </header>

      {children ?? (
        <div className="card placeholder">
          <span>Bu ekran tasarım dosyası (.dc.html) çekildikten sonra inşa edilecek.</span>
          {specRef && (
            <span>
              Spesifikasyon: <code>{specRef}</code>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
