import { useState } from "react";
import { EmptyState, ErrorState, Skeleton } from "@/components/States";
import {
  useCreateJournalEntry,
  useDeleteJournalEntry,
  useJournal,
  useWatchlist,
} from "@/hooks/useApi";
import { timeAgo } from "@/utils/format";
import "./journal.css";

export function JournalPage() {
  const [filter, setFilter] = useState<string>("all");
  const [draft, setDraft] = useState("");
  const [draftSymbol, setDraftSymbol] = useState("");

  const { data: watchlist } = useWatchlist();
  const { data, isLoading, error, refetch } = useJournal(filter === "all" ? undefined : filter);
  const create = useCreateJournalEntry();
  const remove = useDeleteJournalEntry();

  function addEntry() {
    if (!draft.trim()) return;
    create.mutate(
      { symbol: draftSymbol || null, content: draft.trim() },
      {
        onSuccess: () => {
          setDraft("");
          setDraftSymbol("");
        },
      }
    );
  }

  const symbols = watchlist?.items.map((i) => i.symbol) ?? [];

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Günlük</h1>
        <p className="page-subtitle">Sembol bazlı ve genel işlem/analiz notları</p>
      </header>

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
            {symbols.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button className="btn btn--primary" onClick={addEntry} disabled={!draft.trim() || create.isPending}>
            {create.isPending ? "Kaydediliyor…" : "Kaydet"}
          </button>
        </div>
      </section>

      <div className="symbol-picker" style={{ margin: "var(--space-5) 0" }}>
        <button className={`symbol-chip${filter === "all" ? " symbol-chip--active" : ""}`} onClick={() => setFilter("all")}>
          Tümü
        </button>
        {symbols.map((s) => (
          <button key={s} className={`symbol-chip${filter === s ? " symbol-chip--active" : ""}`} onClick={() => setFilter(s)}>
            {s}
          </button>
        ))}
      </div>

      {isLoading && <Skeleton height={120} count={2} />}
      {error && <ErrorState error={error} onRetry={() => refetch()} />}

      {data && data.items.length === 0 && <EmptyState title="Bu filtre için not yok." />}

      {data && data.items.length > 0 && (
        <div className="journal-list">
          {data.items.map((e) => (
            <article key={e.id} className="ui-card ui-card--pad journal-entry">
              <div className="journal-entry__head">
                <span className="journal-entry__tag">{e.symbol ?? "Genel"}</span>
                <span className="muted journal-entry__time">{timeAgo(e.created_at)}</span>
                <button className="journal-entry__del" onClick={() => remove.mutate(e.id)} aria-label="Sil">
                  ✕
                </button>
              </div>
              <p className="journal-entry__body">{e.content}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
