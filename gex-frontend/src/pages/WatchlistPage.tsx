import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkline } from "@/components/Sparkline";
import { RegimeBadge } from "@/components/RegimeBadge";
import { EmptyState, ErrorState, RefreshingDot, Skeleton } from "@/components/States";
import { useAddToWatchlist, useRemoveFromWatchlist, useSymbolSearch, useWatchlist } from "@/hooks/useApi";
import { gexShort, money, pct, strike as fmtStrike } from "@/utils/format";

export function WatchlistPage() {
  const navigate = useNavigate();
  const { data, isLoading, isFetching, error, refetch } = useWatchlist();
  const [query, setQuery] = useState("");
  const { data: search } = useSymbolSearch(query);
  const addMutation = useAddToWatchlist();
  const removeMutation = useRemoveFromWatchlist();

  return (
    <div>
      <header className="page-header dash-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">İzleme Listesi<RefreshingDot active={isFetching} /></h1>
          <p className="page-subtitle">{data ? `${data.items.length} sembol izleniyor` : "Yükleniyor…"}</p>
        </div>
        <input
          className="journal-select"
          style={{ minWidth: 220 }}
          placeholder="Sembol ara ve ekle…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </header>

      {query && search && (
        <section className="ui-card" style={{ marginBottom: "var(--space-5)" }}>
          {search.results.length === 0 ? (
            <p className="muted" style={{ padding: "var(--space-4)" }}>Sonuç yok.</p>
          ) : (
            <ul style={{ listStyle: "none" }}>
              {search.results.map((r) => (
                <li
                  key={r.symbol}
                  style={{
                    display: "flex", alignItems: "center", gap: "var(--space-3)",
                    padding: "var(--space-3) var(--space-4)", borderTop: "1px solid var(--color-border)",
                  }}
                >
                  <span className="cell-strong" style={{ minWidth: 48 }}>{r.symbol}</span>
                  <span className="muted" style={{ flex: 1, fontSize: "var(--text-sm)" }}>{r.company_name}</span>
                  <button
                    className="btn btn--primary"
                    disabled={r.already_in_watchlist || addMutation.isPending}
                    onClick={() => addMutation.mutate(r.symbol, { onSuccess: () => setQuery("") })}
                  >
                    {r.already_in_watchlist ? "Listede" : "+ Ekle"}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {isLoading && <Skeleton height={340} />}
      {error && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && data.items.length === 0 && !isLoading && (
        <EmptyState title="İzleme listeniz boş" hint="Yukarıdaki arama kutusundan sembol ekleyin." />
      )}

      {data && data.items.length > 0 && (
        <section className="ui-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sembol</th><th>Fiyat</th><th>Değişim</th><th>Net GEX</th>
                <th>Gamma Flip</th><th>Flip Mesafesi</th><th>Rejim</th><th>Trend</th><th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((b) => (
                <tr key={b.symbol} style={{ cursor: "pointer" }}>
                  <td onClick={() => navigate(`/symbols/${b.symbol}`)}>
                    <div className="cell-strong">{b.symbol}</div>
                    <div className="muted" style={{ fontSize: "var(--text-xs)" }}>{b.company_name}</div>
                  </td>
                  <td className="num cell-strong">{b.spot_price != null ? money(b.spot_price) : "—"}</td>
                  <td className={`num ${(b.daily_change_pct ?? 0) >= 0 ? "pos" : "neg"}`}>
                    {b.daily_change_pct != null ? pct(b.daily_change_pct) : "—"}
                  </td>
                  <td className={`num ${(b.total_net_gex ?? 0) >= 0 ? "pos" : "neg"}`}>
                    {b.total_net_gex != null ? gexShort(b.total_net_gex) : "—"}
                  </td>
                  <td className="num">{b.gamma_flip_strike != null ? fmtStrike(b.gamma_flip_strike) : "—"}</td>
                  <td className="num">
                    {b.flip_distance != null ? `${b.flip_distance >= 0 ? "+" : ""}${b.flip_distance.toFixed(2)}$` : "—"}
                  </td>
                  <td style={{ textAlign: "right" }}>{b.regime && <RegimeBadge regime={b.regime} compact />}</td>
                  <td style={{ textAlign: "right" }}>
                    <Sparkline data={b.sparkline.length > 1 ? b.sparkline : [0, 0]} />
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button
                      className="journal-entry__del"
                      title="Listeden çıkar"
                      onClick={() => removeMutation.mutate(b.symbol)}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
