/**
 * Merkezi API istemcisi — Build Spec Bölüm 10.1.
 *
 * Token stratejisi (Bölüm 11.1 / Faz 6 notu):
 *  - access token YALNIZCA bellekte tutulur (XSS'te çalınması zorlaşsın diye)
 *  - refresh token localStorage'da — spec httpOnly cookie öneriyor; backend
 *    henüz cookie set etmediği için şimdilik localStorage.
 *    TODO(guvenlik): backend refresh'i httpOnly cookie ile verince buraya geç.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const REFRESH_KEY = "gex.refresh_token";

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

type Listener = (authenticated: boolean) => void;

class ApiClient {
  private accessToken: string | null = null;
  private listeners = new Set<Listener>();
  private refreshing: Promise<boolean> | null = null;

  // ---- token yönetimi ----
  setTokens(access: string | null, refresh?: string | null): void {
    this.accessToken = access;
    if (refresh !== undefined) {
      try {
        if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
        else localStorage.removeItem(REFRESH_KEY);
      } catch {
        /* private mode vb. */
      }
    }
    this.listeners.forEach((l) => l(Boolean(access)));
  }

  getRefreshToken(): string | null {
    try {
      return localStorage.getItem(REFRESH_KEY);
    } catch {
      return null;
    }
  }

  hasSession(): boolean {
    return Boolean(this.accessToken) || Boolean(this.getRefreshToken());
  }

  onAuthChange(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  clear(): void {
    this.setTokens(null, null);
  }

  /** Refresh token ile yeni access token alır. Aynı anda tek istek yapılır. */
  async refreshAccessToken(): Promise<boolean> {
    if (this.refreshing) return this.refreshing;

    const refresh = this.getRefreshToken();
    if (!refresh) return false;

    this.refreshing = (async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) {
          this.clear();
          return false;
        }
        const body = await res.json();
        this.setTokens(body.access_token);
        return true;
      } catch {
        return false;
      } finally {
        this.refreshing = null;
      }
    })();

    return this.refreshing;
  }

  // ---- istek ----
  async request<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {}),
        ...options.headers,
      },
    });

    // Süresi dolmuş access token -> bir kez yenilemeyi dene
    if (res.status === 401 && retry && this.getRefreshToken()) {
      const ok = await this.refreshAccessToken();
      if (ok) return this.request<T>(path, options, false);
    }

    if (res.status === 204) return undefined as T;

    if (!res.ok) {
      let code = "UNKNOWN";
      let message = "Bir şeyler ters gitti.";
      try {
        const body = await res.json();
        code = body?.error?.code ?? code;
        message = body?.error?.message ?? message;
      } catch {
        /* gövde JSON değil */
      }
      if (res.status === 401) this.clear();
      throw new ApiError(code, message, res.status);
    }

    return res.json() as Promise<T>;
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>(path);
  }
  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
  }
  patch<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined });
  }
  delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }
}

export const apiClient = new ApiClient();
