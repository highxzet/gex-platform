import { useEffect, useRef, useState } from "react";
import { useSymbolSearch } from "@/hooks/useApi";
import "./symbol-search.css";

interface Props {
  value: string;
  onSelect: (symbol: string) => void;
  placeholder?: string;
  /** Hızlı erişim için gösterilecek semboller (genelde izleme listesi). */
  quickPicks?: string[];
}

/**
 * Aranabilir sembol seçici.
 *
 * 500+ sembollü evrende çip listesi kullanılamaz; bu bileşen sunucu tarafı
 * aramayı (GET /api/symbols/search) kullanır ve izleme listesini hızlı erişim
 * olarak sunar.
 */
export function SymbolSearchBox({ value, onSelect, placeholder = "Sembol ara…", quickPicks = [] }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const boxRef = useRef<HTMLDivElement>(null);

  const { data, isFetching } = useSymbolSearch(query);
  const results = data?.results ?? [];

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function choose(symbol: string) {
    onSelect(symbol);
    setQuery("");
    setOpen(false);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => (h + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => (h - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      choose(results[highlight].symbol);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div className="symsearch" ref={boxRef}>
      <div className="symsearch__row">
        <span className="symsearch__current">{value || "—"}</span>
        <input
          className="symsearch__input"
          value={query}
          placeholder={placeholder}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            setHighlight(0);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {isFetching && <span className="symsearch__spin" />}
      </div>

      {open && (
        <div className="symsearch__panel">
          {query.trim() === "" && quickPicks.length > 0 && (
            <>
              <div className="symsearch__label">İzleme listem</div>
              <div className="symsearch__quick">
                {quickPicks.map((s) => (
                  <button key={s} className="symbol-chip" onClick={() => choose(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </>
          )}

          {query.trim() !== "" && results.length === 0 && !isFetching && (
            <div className="symsearch__empty">Sonuç yok</div>
          )}

          {results.map((r, i) => (
            <button
              key={r.symbol}
              className={`symsearch__item${i === highlight ? " symsearch__item--active" : ""}`}
              onMouseEnter={() => setHighlight(i)}
              onClick={() => choose(r.symbol)}
            >
              <span className="symsearch__ticker">{r.symbol}</span>
              <span className="symsearch__name">{r.company_name}</span>
              {r.already_in_watchlist && <span className="symsearch__badge">listede</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
