import { useNavigate } from "react-router-dom";
import { Sparkline } from "@/components/Sparkline";
import { RegimeBadge } from "@/components/RegimeBadge";
import { BANKS } from "@/mocks/data";
import { gexShort, money, pct, strike as fmtStrike } from "@/utils/format";

export function WatchlistPage() {
  const navigate = useNavigate();

  return (
    <div>
      <header className="page-header dash-header" style={{ display: "flex", justifyContent: "space-between" }}>
        <div>
          <h1 className="page-title">İzleme Listesi</h1>
          <p className="page-subtitle">{BANKS.length} sembol izleniyor</p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <button className="btn btn--ghost">Filtre</button>
          <button className="btn btn--primary">+ Sembol ekle</button>
        </div>
      </header>

      <section className="ui-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Sembol</th>
              <th>Fiyat</th>
              <th>Değişim</th>
              <th>Net GEX</th>
              <th>Gamma Flip</th>
              <th>Flip Mesafesi</th>
              <th>Rejim</th>
              <th>7g</th>
            </tr>
          </thead>
          <tbody>
            {BANKS.map((b) => {
              const flipDist = b.gamma_flip_strike != null ? b.spot_price - b.gamma_flip_strike : null;
              return (
                <tr key={b.symbol} onClick={() => navigate(`/symbols/${b.symbol}`)} style={{ cursor: "pointer" }}>
                  <td>
                    <div className="cell-strong">{b.symbol}</div>
                    <div className="muted" style={{ fontSize: "var(--text-xs)" }}>{b.company_name}</div>
                  </td>
                  <td className="num cell-strong">{money(b.spot_price)}</td>
                  <td className={`num ${b.daily_change_pct >= 0 ? "pos" : "neg"}`}>{pct(b.daily_change_pct)}</td>
                  <td className={`num ${b.total_net_gex >= 0 ? "pos" : "neg"}`}>{gexShort(b.total_net_gex)}</td>
                  <td className="num">{b.gamma_flip_strike != null ? fmtStrike(b.gamma_flip_strike) : "—"}</td>
                  <td className="num">{flipDist != null ? `${flipDist >= 0 ? "+" : ""}${flipDist.toFixed(2)}$` : "—"}</td>
                  <td style={{ textAlign: "right" }}>
                    <RegimeBadge regime={b.regime} compact />
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <Sparkline data={b.sparkline} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
