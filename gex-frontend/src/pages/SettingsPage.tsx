import { useState } from "react";
import { Segment } from "@/components/Segment";
import "./settings.css";

const SUB_NAV = [
  { value: "profile", label: "Profil" },
  { value: "watchlist", label: "İzleme listesi yönetimi" },
  { value: "notifications", label: "Bildirim tercihleri" },
  { value: "appearance", label: "Görünüm" },
  { value: "privacy", label: "Veri ve gizlilik" },
  { value: "api", label: "API erişimi" },
];

type Theme = "dark" | "light" | "system";
type Density = "standard" | "compact";

export function SettingsPage() {
  const [section, setSection] = useState("appearance");
  const [theme, setTheme] = useState<Theme>("dark");
  const [density, setDensity] = useState<Density>("standard");

  function applyTheme(next: Theme) {
    setTheme(next);
    const root = document.documentElement;
    if (next === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", next);
  }
  function applyDensity(next: Density) {
    setDensity(next);
    document.documentElement.setAttribute("data-density", next);
  }

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Ayarlar</h1>
      </header>

      <div className="settings-layout">
        <nav className="settings-subnav">
          {SUB_NAV.map((s) => (
            <button
              key={s.value}
              className={`settings-subnav__item${section === s.value ? " settings-subnav__item--active" : ""}`}
              onClick={() => setSection(s.value)}
            >
              {s.label}
            </button>
          ))}
        </nav>

        <div className="settings-content">
          {section === "appearance" && (
            <>
              <div className="settings-block">
                <h3 className="settings-block__title">Tema</h3>
                <Segment
                  value={theme}
                  onChange={applyTheme}
                  options={[
                    { value: "dark", label: "Koyu" },
                    { value: "light", label: "Açık" },
                    { value: "system", label: "Sistem" },
                  ]}
                />
              </div>
              <div className="settings-block">
                <h3 className="settings-block__title">Yoğunluk</h3>
                <Segment
                  value={density}
                  onChange={applyDensity}
                  options={[
                    { value: "standard", label: "Standart" },
                    { value: "compact", label: "Kompakt" },
                  ]}
                />
                <p className="settings-block__hint">
                  Kompakt mod tablo satır yüksekliğini 40px'ten 32px'e indirir; çok ekranlı, veri yoğun kullanım için.
                </p>
              </div>
            </>
          )}

          {section === "privacy" && (
            <>
              <div className="settings-block">
                <h3 className="settings-block__title">Hesap verileri</h3>
                <p className="settings-block__hint">Tüm verilerinizi (izleme listesi, uyarılar, notlar) indirilebilir JSON olarak dışa aktarın.</p>
                <button className="btn btn--ghost" style={{ marginTop: "var(--space-3)" }}>Verilerimi indir</button>
              </div>
              <div className="settings-block">
                <h3 className="settings-block__title">Hesabı sil</h3>
                <p className="settings-block__hint">Bu işlem geri alınamaz. Hesabınız ve tüm ilişkili veriler kalıcı olarak silinir.</p>
                <button className="btn btn--danger" style={{ marginTop: "var(--space-3)" }}>Hesabı sil</button>
              </div>
            </>
          )}

          {section !== "appearance" && section !== "privacy" && (
            <div className="ui-card ui-card--pad placeholder">
              <span>Bu ayar bölümü sonraki fazda tamamlanacak.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
