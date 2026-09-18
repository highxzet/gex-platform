import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { apiClient } from "@/api/client";
import type { LoginResponse, User } from "@/api/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Sayfa yenilendiğinde: access token bellekte olmadığı için refresh ile oturumu kur
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!apiClient.getRefreshToken()) {
        setLoading(false);
        return;
      }
      const ok = await apiClient.refreshAccessToken();
      if (ok) {
        try {
          const me = await apiClient.get<User>("/api/auth/me");
          if (!cancelled) setUser(me);
        } catch {
          apiClient.clear();
        }
      }
      if (!cancelled) setLoading(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string, rememberMe: boolean) => {
    const res = await apiClient.post<LoginResponse>("/api/auth/login", {
      email,
      password,
      remember_me: rememberMe,
    });
    apiClient.setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
    // Kullanıcının kayıtlı görünüm tercihlerini uygula
    document.documentElement.setAttribute("data-theme", res.user.theme_preference === "system" ? "dark" : res.user.theme_preference);
    document.documentElement.setAttribute("data-density", res.user.density_preference);
  }, []);

  const logout = useCallback(() => {
    apiClient.clear();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth, AuthProvider içinde kullanılmalı");
  return ctx;
}
