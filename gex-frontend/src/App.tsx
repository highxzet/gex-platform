import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SymbolDetailPage } from "./pages/SymbolDetailPage";
import { WatchlistPage } from "./pages/WatchlistPage";
import { ComparePage } from "./pages/ComparePage";
import { HistoryPage } from "./pages/HistoryPage";
import { AlertsPage } from "./pages/AlertsPage";
import { JournalPage } from "./pages/JournalPage";
import { MethodologyPage } from "./pages/MethodologyPage";
import { DataStatusPage } from "./pages/DataStatusPage";
import { SettingsPage } from "./pages/SettingsPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="/symbols" element={<SymbolDetailPage />} />
        <Route path="/symbols/:ticker" element={<SymbolDetailPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
        <Route path="/data-status" element={<DataStatusPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}
