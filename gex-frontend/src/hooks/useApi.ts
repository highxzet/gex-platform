/** Backend endpoint'lerine bağlı React Query hook'ları — Build Spec Bölüm 10.2. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type {
  AlertListResponse,
  DashboardResponse,
  DataStatusResponse,
  GexProfileResponse,
  JournalListResponse,
  NotificationListResponse,
  RawDataResponse,
  SymbolSearchResponse,
  TimeSeriesResponse,
  WatchlistResponse,
} from "@/api/types";

/** Canlı veri: 90 sn'de bir arka planda yenilenir (tasarım Bölüm 7.2 "yenileniyor" durumu). */
const LIVE = { refetchInterval: 90_000, staleTime: 60_000 } as const;

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiClient.get<DashboardResponse>("/api/dashboard"),
    ...LIVE,
  });
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: () => apiClient.get<WatchlistResponse>("/api/watchlist"),
    ...LIVE,
  });
}

export function useGexProfile(ticker: string | undefined) {
  return useQuery({
    queryKey: ["gex-profile", ticker],
    queryFn: () => apiClient.get<GexProfileResponse>(`/api/symbols/${ticker}/gex-profile`),
    enabled: Boolean(ticker),
    ...LIVE,
  });
}

export function useTimeSeries(ticker: string | undefined, range: "7d" | "30d" | "90d") {
  return useQuery({
    queryKey: ["time-series", ticker, range],
    queryFn: () => apiClient.get<TimeSeriesResponse>(`/api/symbols/${ticker}/time-series?range=${range}`),
    enabled: Boolean(ticker),
  });
}

export function useRawData(ticker: string | undefined, page = 1, pageSize = 50) {
  return useQuery({
    queryKey: ["raw-data", ticker, page, pageSize],
    queryFn: () =>
      apiClient.get<RawDataResponse>(`/api/symbols/${ticker}/raw-data?page=${page}&page_size=${pageSize}`),
    enabled: Boolean(ticker),
  });
}

export function useSymbolSearch(query: string) {
  return useQuery({
    queryKey: ["symbol-search", query],
    queryFn: () => apiClient.get<SymbolSearchResponse>(`/api/symbols/search?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 0,
  });
}

export function useDataStatus() {
  return useQuery({
    queryKey: ["data-status"],
    queryFn: () => apiClient.get<DataStatusResponse>("/api/data-status"),
    refetchInterval: 120_000,
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: () => apiClient.get<AlertListResponse>("/api/alerts"),
  });
}

export function useToggleAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      apiClient.patch(`/api/alerts/${id}`, { enabled }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: () => apiClient.get<NotificationListResponse>("/api/notifications"),
  });
}

export function useJournal(symbol?: string) {
  return useQuery({
    queryKey: ["journal", symbol ?? "all"],
    queryFn: () =>
      apiClient.get<JournalListResponse>(`/api/journal${symbol ? `?symbol=${symbol}` : ""}`),
  });
}

export function useCreateJournalEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { symbol: string | null; content: string }) =>
      apiClient.post("/api/journal", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["journal"] }),
  });
}

export function useDeleteJournalEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/journal/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["journal"] }),
  });
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => apiClient.post("/api/watchlist", { symbol }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => apiClient.delete(`/api/watchlist/${symbol}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["watchlist"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
