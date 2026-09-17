import { useMemo, useState } from "react";
import { BANKS, MOCK_JOURNAL, type JournalEntry } from "@/mocks/data";
import { timeAgo } from "@/utils/format";
import "./journal.css";

export function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>(MOCK_JOURNAL);
  const [filter, setFilter] = useState<string>("all");
  const [draft, setDraft] = useState("");
  const [draftSymbol, setDraftSymbol] = useState<string>("");

  const filtered = useMemo(
    () => (filter === "all" ? entries : entries.filter((e) => e.symbol === filter)),
    [entries, filter]
  );

  function addEntry() {
    if (!draft.trim()) return;
    setEntries((prev) => [
      { id: crypto.randomUUID(), symbol: draftSymbol || null, content: draft.trim(), created_at: new Date().toISOString() },
      ...prev,
    ]);
    setDraft("");
    setDraftSymbol("");
  }

  function remove(id: string) {
    setEntries((prev) => prev.filter((e) => e.id !== id));
  }

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Günlük</h1>
        <p className="page-subtitle">Sembol bazlı ve genel işlem/analiz notları</p>
      </header>

      {/* Composer */}
      <section className="ui-card ui-card--pad journal-composer">
        <textarea
          className="sd-notes"
          rows={3}
          placeholder="Bir not ekle... (örn. 'JPM flip altına düştü, izliyorum')"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        <div className="journal-composer__actions">
          <select className="journal-select" value={draftSymbol} onChange={(e) => setDraftSymbol(e.target.value)}>
            <option value="">Genel not</option>
            {BANKS.map((b) => (
              <option key={b.symbol} value={b.symbol}>
                {b.symbol}
              </option>
            ))}
          </select>
          <button className="btn btn--primary" onClick={addEntry} disabled={!draft.trim()}>
            Kaydet
          </button>
        </div>
      </section>

      {/* Filtre */}
      <div className="symbol-picker" style={{ margin: "var(--space-5) 0" }}>
        <button className={`symbol-chip${filter === "all" ? " symbol-chip--active" : ""}`} onClick={() => setFilter("all")}>
          Tümü
        </button>
        {Array.from(new Set(entries.map((e) => e.symbol).filter(Boolean) as string[])).map((sym) => (
          <button key={sym} className={`symbol-chip${filter === sym ? " symbol-chip--active" : ""}`} onClick={() => setFilter(sym)}>
            {sym}
          </button>
        ))}
      </div>

      {/* Liste */}
      <div className="journal-list">
        {filtered.length === 0 && <p className="muted">Bu filtre için not yok.</p>}
        {filtered.map((e) => (
          <article key={e.id} className="ui-card ui-card--pad journal-entry">
            <div className="journal-entry__head">
              <span className="journal-entry__tag">{e.symbol ?? "Genel"}</span>
              <span className="muted journal-entry__time">{timeAgo(e.created_at)}</span>
              <button className="journal-entry__del" onClick={() => remove(e.id)} aria-label="Sil">
                ✕
              </button>
            </div>
            <p className="journal-entry__body">{e.content}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
