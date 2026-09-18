import { Link } from "react-router-dom";
import { RegimeBadge } from "@/components/RegimeBadge";
import { Sparkline } from "@/components/Sparkline";
import { EmptyState, ErrorState, RefreshingDot, Skeleton } from "@/components/States";
import { useDashboard } from "@/hooks/useApi";
import { gexShort, money, pct, timeAgo } from "@/utils/format";
import "./dashboard.css";

export function DashboardPage() {
  const { data, isLoading, isFetching, error, refetch } = useDashboard();

  if (isLoading) {
    return (
      <div>
        <header className="page-header">
          <h1 className="page-title">Ana Panel</h1>
        </header>
        <Skeleton height={92} count={1} />
        <div style={{ marginTop: "var(--space-6)" }}>
          <Skeleton height={220} count={2} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <header className="page-header">
          <h1 className="page-title">Ana Panel</h1>
        </header>
        <ErrorState error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  const d = data!;
  const hasData = d.summary_strip.length > 0;

  return (
    <div>
      <header className="page-header dash-header">
        <div>
          <h1 className="page-title">
            Ana Panel
            <RefreshingDot active={isFetching} />
          </h1>
          <p className="page-subtitle">İzlenen bankacılık sembollerinin gamma exposure özeti</p>
        </div>
        {d.last_updated && (
          <span className="dash-updated">Son güncelleme: {timeAgo(d.last_updated)}</span>
        )}
      </header>

      {!hasData && (
        <EmptyState
          title="İzleme listeniz boş"
          hint={<>Başlamak için <Link to="/watchlist" className="dash-link">İzleme Listesi</Link>'ne sembol ekleyin.</>}
        />
      )}

      {hasData && (
        <>
          <section className="summary-strip">
            {d.summary_strip.map((s) => (
              <Link key={s.symbol} to={`/symbols/${s.symbol}`} className="summary-card">
                <div className="summary-card__top">
                  <span className="summary-card__symbol">{s.symbol}</span>
                  <RegimeBadge regime={s.regime} compact />
                </div>
                <div className="summary-card__price num">{money(s.spot_price)}</div>
                <div className="summary-card__bottom">
                  <span className={`num ${(s.daily_change_pct ?? 0) >= 0 ? "pos" : "neg"}`}>
                    {s.daily_change_pct != null ? pct(s.daily_change_pct) : "—"}
                  </span>
                  <span className={s.is_stale ? "neg" : "muted"}>{s.data_age_minutes} dk</span>
                </div>
              </Link>
            ))}
          </section>

          <div className="dash-grid">
            <section className="ui-card ui-card--pad">
              <h2 className="ui-card__title">Dikkat Gerektirenler</h2>
              {d.attention_items.length === 0 ? (
                <p className="muted" style={{ marginTop: "var(--space-4)", fontSize: "var(--text-sm)" }}>
                  Şu an dikkat gerektiren bir durum yok.
                </p>
              ) : (
                <ul className="attention-list">
                  {d.attention_items.map((a, i) => (
                    <li key={`${a.symbol}-${i}`} className="attention-item">
                      <Link to={`/symbols/${a.symbol}`} className="attention-item__symbol">
                        {a.symbol}
                      </Link>
                      <span className="attention-item__msg">{a.message}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="ui-card ui-card--pad">
              <div className="dash-card-head">
                <h2 className="ui-card__title">İzleme Listesi</h2>
                <Link to="/watchlist" className="dash-link">Tümünü gör →</Link>
              </div>
              <ul className="watch-preview">
                {d.watchlist_preview.map((w) => (
                  <li key={w.symbol} className="watch-preview__row">
                    <Link to={`/symbols/${w.symbol}`} className="watch-preview__symbol">{w.symbol}</Link>
                    <span className="watch-preview__price num">{money(w.spot_price)}</span>
                    <span className={`watch-preview__gex num ${w.total_net_gex >= 0 ? "pos" : "neg"}`}>
                      {gexShort(w.total_net_gex)}
                    </span>
                    <Sparkline data={w.sparkline.length > 1 ? w.sparkline : [0, 0]} />
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
