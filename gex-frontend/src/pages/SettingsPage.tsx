import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { Segment } from "@/components/Segment";
import { useAuth } from "@/auth/AuthContext";
import type { User } from "@/api/types";
import "./settings.css";

const SUB_NAV = [
  { value: "profile", label: "Profil" },
  { value: "appearance", label: "Görünüm" },
  { value: "privacy", label: "Veri ve gizlilik" },
];

type Theme = "dark" | "light" | "system";
type Density = "standard" | "compact";

export function SettingsPage() {
  const { user, logout } = useAuth();
  const [section, setSection] = useState("appearance");
  const [theme, setTheme] = useState<Theme>((user?.theme_preference as Theme) ?? "dark");
  const [density, setDensity] = useState<Density>((user?.density_preference as Density) ?? "standard");
  const [displayName, setDisplayName] = useState(user?.display_name ?? "");
  const [saved, setSaved] = useState<string | null>(null);

  const saveAppearance = useMutation({
    mutationFn: (payload: { theme?: Theme; density?: Density }) =>
      apiClient.patch<User>("/api/settings/appearance", payload),
    onSuccess: () => setSaved("Görünüm tercihleri kaydedildi."),
  });

  const saveProfile = useMutation({
    mutationFn: (payload: { display_name: string }) =>
      apiClient.patch<User>("/api/settings/profile", payload),
    onSuccess: () => setSaved("Profil güncellendi."),
  });

  function applyTheme(next: Theme) {
    setTheme(next);
    const root = document.documentElement;
    if (next === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", next);
    saveAppearance.mutate({ theme: next });
  }

  function applyDensity(next: Density) {
    setDensity(next);
    document.documentElement.setAttribute("data-density", next);
    saveAppearance.mutate({ density: next });
  }

  async function exportData() {
    const data = await apiClient.get<unknown>("/api/settings/export-data");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "gex-verilerim.json";
    a.click();
    URL.revokeObjectURL(url);
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
              onClick={() => { setSection(s.value); setSaved(null); }}
            >
              {s.label}
            </button>
          ))}
        </nav>

        <div className="settings-content">
          {saved && <p className="muted" style={{ marginBottom: "var(--space-4)", color: "var(--color-positive)" }}>{saved}</p>}

          {section === "profile" && (
            <div className="settings-block">
              <h3 className="settings-block__title">Profil</h3>
              <p className="settings-block__hint">E-posta: {user?.email}</p>
              <label className="login-field" style={{ marginTop: "var(--space-4)", maxWidth: 320 }}>
                <span>Görünen ad</span>
                <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
              </label>
              <button
                className="btn btn--primary"
                style={{ marginTop: "var(--space-3)" }}
                onClick={() => saveProfile.mutate({ display_name: displayName })}
                disabled={saveProfile.isPending}
              >
                Kaydet
              </button>
            </div>
          )}

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
                  Kompakt mod tablo satır yüksekliğini azaltır; çok ekranlı, veri yoğun kullanım için.
                </p>
              </div>
            </>
          )}

          {section === "privacy" && (
            <>
              <div className="settings-block">
                <h3 className="settings-block__title">Hesap verileri</h3>
                <p className="settings-block__hint">
                  Tüm verilerinizi (izleme listesi, uyarılar, notlar) indirilebilir JSON olarak dışa aktarın.
                </p>
                <button className="btn btn--ghost" style={{ marginTop: "var(--space-3)" }} onClick={exportData}>
                  Verilerimi indir
                </button>
              </div>
              <div className="settings-block">
                <h3 className="settings-block__title">Oturum</h3>
                <p className="settings-block__hint">Bu cihazdaki oturumu kapatır.</p>
                <button className="btn btn--danger" style={{ marginTop: "var(--space-3)" }} onClick={logout}>
                  Çıkış yap
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
