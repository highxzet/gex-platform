import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./login.css";

/**
 * Giriş ekranı — Tasarım dokümanı Bölüm 5.1.
 * Skeleton: form UI hazır; gerçek `POST /api/auth/login` bağlantısı Faz 6'da.
 */
export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // TODO(auth): Faz 6 — apiClient.post('/api/auth/login', { email, password })
    navigate("/");
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">GEX</div>
        <h1 className="login-title">Oturum aç</h1>
        <p className="login-subtitle">Gamma Exposure analiz platformu</p>

        <label className="login-field">
          <span>E-posta</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
          />
        </label>

        <label className="login-field">
          <span>Şifre</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </label>

        <label className="login-remember">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          <span>Beni hatırla</span>
        </label>

        <button type="submit" className="login-submit">
          Giriş yap
        </button>
      </form>
    </div>
  );
}
