import { Link } from "react-router-dom";
import { RegimeBadge } from "@/components/RegimeBadge";
import { Sparkline } from "@/components/Sparkline";
import { mockDashboard } from "@/mocks/data";
import { gexShort, money, pct, timeAgo } from "@/utils/format";
import "./dashboard.css";

export function DashboardPage() {
  const data = mockDashboard();

  return (
    <div>
      <header className="page-header dash-header">
        <div>
          <h1 className="page-title">Ana Panel</h1>
          <p className="page-subtitle">İzlenen bankacılık sembollerinin gamma exposure özeti</p>
        </div>
        <span className="dash-updated">Son güncelleme: {timeAgo(data.last_updated)}</span>
      </header>

      {/* Özet şeridi */}
      <section className="summary-strip">
        {data.summary_strip.map((s) => (
          <Link key={s.symbol} to={`/symbols/${s.symbol}`} className="summary-card">
            <div className="summary-card__top">
              <span className="summary-card__symbol">{s.symbol}</span>
              <RegimeBadge regime={s.regime} compact />
            </div>
            <div className="summary-card__price num">{money(s.spot_price)}</div>
            <div className="summary-card__bottom">
              <span className={`num ${s.daily_change_pct >= 0 ? "pos" : "neg"}`}>{pct(s.daily_change_pct)}</span>
              <span className="muted">{s.data_age_minutes} dk</span>
            </div>
          </Link>
        ))}
      </section>

      <div className="dash-grid">
        {/* Dikkat gerektirenler */}
        <section className="ui-card ui-card--pad">
          <h2 className="ui-card__title">Dikkat Gerektirenler</h2>
          <ul className="attention-list">
            {data.attention_items.map((a, i) => (
              <li key={i} className="attention-item">
                <Link to={`/symbols/${a.symbol}`} className="attention-item__symbol">
                  {a.symbol}
                </Link>
                <span className="attention-item__msg">{a.message}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* İzleme listesi önizlemesi */}
        <section className="ui-card ui-card--pad">
          <div className="dash-card-head">
            <h2 className="ui-card__title">İzleme Listesi</h2>
            <Link to="/watchlist" className="dash-link">
              Tümünü gör →
            </Link>
          </div>
          <ul className="watch-preview">
            {data.watchlist_preview.map((w) => (
              <li key={w.symbol} className="watch-preview__row">
                <Link to={`/symbols/${w.symbol}`} className="watch-preview__symbol">
                  {w.symbol}
                </Link>
                <span className="watch-preview__price num">{money(w.spot_price)}</span>
                <span className={`watch-preview__gex num ${w.total_net_gex >= 0 ? "pos" : "neg"}`}>
                  {gexShort(w.total_net_gex)}
                </span>
                <Sparkline data={w.sparkline} />
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
