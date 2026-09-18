import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "@/api/client";
import { useAuth } from "@/auth/AuthContext";
import { messageForCode } from "@/utils/errorMessages";
import "./login.css";

/** Giriş ekranı — Tasarım Bölüm 5.1, API Bölüm 7.2. */
export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: { pathname: string } } };
  const { user, login } = useAuth();

  const [email, setEmail] = useState("kurucu@gexplatform.com");
  const [password, setPassword] = useState("gexdev2026");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password, remember);
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? messageForCode(err.code, err.message)
          : "Sunucuya ulaşılamadı. Backend çalışıyor mu?"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">GEX</div>
        <h1 className="login-title">Oturum aç</h1>
        <p className="login-subtitle">Gamma Exposure analiz platformu</p>

        {error && <div className="login-error">{error}</div>}

        <label className="login-field">
          <span>E-posta</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
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
            required
          />
        </label>

        <label className="login-remember">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          <span>Beni hatırla</span>
        </label>

        <button type="submit" className="login-submit" disabled={submitting}>
          {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
        </button>
      </form>
    </div>
  );
}
