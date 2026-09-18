import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { useNotifications } from "@/hooks/useApi";
import "./layout.css";

interface NavItem {
  to: string;
  label: string;
  end?: boolean;
  badge?: number;
}

const PRIMARY_NAV: NavItem[] = [
  { to: "/", label: "Ana Panel", end: true },
  { to: "/symbols", label: "Hisse Analizi" },
  { to: "/watchlist", label: "İzleme Listesi" },
  { to: "/compare", label: "Karşılaştır" },
  { to: "/history", label: "Geçmiş / Backtest" },
  { to: "/alerts", label: "Uyarılar" },
  { to: "/journal", label: "Günlük" },
];

const SECONDARY_NAV: NavItem[] = [
  { to: "/methodology", label: "Metodoloji" },
  { to: "/data-status", label: "Veri Durumu" },
  { to: "/settings", label: "Ayarlar" },
];

function NavGroup({ items }: { items: NavItem[] }) {
  return (
    <nav className="nav-group">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `nav-item${isActive ? " nav-item--active" : ""}`}
        >
          <span className="nav-item__dot" aria-hidden />
          {item.label}
          {item.badge ? <span className="nav-item__badge">{item.badge}</span> : null}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: notifications } = useNotifications();

  const primary = PRIMARY_NAV.map((item) =>
    item.to === "/alerts" ? { ...item, badge: notifications?.unread_count || undefined } : item
  );

  const initial = (user?.display_name || user?.email || "?").charAt(0).toLocaleUpperCase("tr");

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">GEX</div>

        <div className="sidebar__nav">
          <NavGroup items={primary} />
          <div className="sidebar__divider" />
          <NavGroup items={SECONDARY_NAV} />
        </div>

        <button className="sidebar__user" type="button" onClick={handleLogout} title="Çıkış yap">
          <span className="sidebar__user-avatar">{initial}</span>
          <span className="sidebar__user-name">{user?.display_name ?? user?.email ?? "—"}</span>
          <span className="sidebar__user-chevron">⎋</span>
        </button>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
