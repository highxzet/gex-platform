import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { DashboardResponse } from "@/api/types";

/**
 * Ana Panel verisi — Build Spec Bölüm 10.2.
 * isLoading (ilk yükleme) ve isFetching (arka plan yenileme) React Query'den gelir.
 */
export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiClient.get<DashboardResponse>("/api/dashboard"),
    refetchInterval: 90_000,
    staleTime: 60_000,
  });
}
