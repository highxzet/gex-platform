import { NavLink, Outlet } from "react-router-dom";
import "./layout.css";

interface NavItem {
  to: string;
  label: string;
  end?: boolean;
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
        </NavLink>
      ))}
    </nav>
  );
}

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">GEX</div>

        <div className="sidebar__nav">
          <NavGroup items={PRIMARY_NAV} />
          <div className="sidebar__divider" />
          <NavGroup items={SECONDARY_NAV} />
        </div>

        <button className="sidebar__user" type="button">
          <span className="sidebar__user-avatar">K</span>
          <span className="sidebar__user-name">kurucu</span>
          <span className="sidebar__user-chevron">›</span>
        </button>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
