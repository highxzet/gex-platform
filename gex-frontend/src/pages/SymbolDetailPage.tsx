import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Tabs } from "@/components/Tabs";
import { RegimeBadge } from "@/components/RegimeBadge";
import { GexProfileChart } from "@/components/GexProfileChart";
import { BANKS, findBank, mockGexProfile } from "@/mocks/data";
import { gexShort, money, pct, strike as fmtStrike, timeAgo } from "@/utils/format";
import "./symbol-detail.css";

const TABS = [
  { value: "gex", label: "GEX Profili" },
  { value: "series", label: "Zaman Serisi" },
  { value: "raw", label: "Ham Veri" },
  { value: "notes", label: "Notlar" },
];

export function SymbolDetailPage() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState("gex");

  const symbol = (ticker ?? "JPM").toUpperCase();
  const bank = findBank(symbol);
  const profile = mockGexProfile(symbol);

  if (!bank || !profile) {
    return (
      <div>
        <h1 className="page-title">Sembol bulunamadı</h1>
        <p className="page-subtitle">'{symbol}' sembolü bulunamadı veya izleme listenizde değil.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Sembol seçici (ana panelden gelmeyince hızlı geçiş) */}
      <div className="symbol-picker">
        {BANKS.map((b) => (
          <button
            key={b.symbol}
            className={`symbol-chip${b.symbol === symbol ? " symbol-chip--active" : ""}`}
            onClick={() => navigate(`/symbols/${b.symbol}`)}
          >
            {b.symbol}
          </button>
        ))}
      </div>

      <header className="sd-header">
        <div>
          <div className="sd-title-row">
            <h1 className="page-title">{bank.symbol}</h1>
            <RegimeBadge regime={bank.regime} />
          </div>
          <p className="page-subtitle">{bank.company_name}</p>
        </div>
        <div className="sd-price">
          <span className="sd-price__value num">{money(bank.spot_price)}</span>
          <span className={`num ${bank.daily_change_pct >= 0 ? "pos" : "neg"}`}>{pct(bank.daily_change_pct)}</span>
        </div>
      </header>

      {/* Metrik kartları */}
      <section className="metric-row">
        <Metric label="Toplam Net GEX" value={gexShort(bank.total_net_gex)} tone={bank.total_net_gex >= 0 ? "pos" : "neg"} />
        <Metric label="Gamma Flip" value={bank.gamma_flip_strike != null ? fmtStrike(bank.gamma_flip_strike) : "—"} />
        <Metric label="Call Wall" value={bank.call_wall_strike != null ? fmtStrike(bank.call_wall_strike) : "—"} tone="pos" />
        <Metric label="Put Wall" value={bank.put_wall_strike != null ? fmtStrike(bank.put_wall_strike) : "—"} tone="neg" />
      </section>

      <Tabs tabs={TABS} active={tab} onChange={setTab} />

      {tab === "gex" && (
        <section className="ui-card ui-card--pad">
          <div className="sd-card-head">
            <h2 className="ui-card__title">GEX Profili (strike bazında net gamma exposure)</h2>
            <span className="muted sd-computed">Hesaplama: {timeAgo(profile.computed_at)}</span>
          </div>
          <GexProfileChart
            strikes={profile.strikes}
            spotPrice={profile.spot_price}
            gammaFlipStrike={profile.gamma_flip_strike}
            callWallStrike={profile.call_wall_strike}
            putWallStrike={profile.put_wall_strike}
          />
        </section>
      )}

      {tab === "raw" && (
        <section className="ui-card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Strike</th>
                <th>Call GEX</th>
                <th>Put GEX</th>
                <th>Net GEX</th>
              </tr>
            </thead>
            <tbody>
              {[...profile.strikes]
                .sort((a, b) => b.strike - a.strike)
                .map((r) => (
                  <tr key={r.strike}>
                    <td className="cell-strong num">{fmtStrike(r.strike)}</td>
                    <td className="num pos">{gexShort(r.call_gex)}</td>
                    <td className="num neg">{gexShort(r.put_gex)}</td>
                    <td className={`num ${r.net_gex >= 0 ? "pos" : "neg"}`}>{gexShort(r.net_gex)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "series" && (
        <section className="ui-card ui-card--pad placeholder">
          <span>Zaman serisi grafiği (son 30 gün Net GEX) — Faz 10.</span>
          <span className="muted">Kaynak: GET /api/symbols/{"{ticker}"}/time-series</span>
        </section>
      )}

      {tab === "notes" && (
        <section className="ui-card ui-card--pad">
          <textarea className="sd-notes" placeholder={`${bank.symbol} için not ekle... (örn. "Flip noktası altına düştü, izliyorum")`} rows={5} />
        </section>
      )}
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "pos" | "neg" }) {
  return (
    <div className="ui-card ui-card--pad metric">
      <span className="ui-card__label">{label}</span>
      <span className={`metric__value num ${tone ?? ""}`}>{value}</span>
    </div>
  );
}
