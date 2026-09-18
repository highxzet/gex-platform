"""Sembol evrenini (S&P 500 + NASDAQ-100) Wikipedia'dan tazeler.

    python -m app.scripts.refresh_universe

`app/data/universe.py` dosyasını yeniden üretir. Endeks bileşenleri yılda birkaç
kez değiştiği için bu script elle, seyrek çalıştırılır — uygulama çalışma anında
ağa BAĞIMLI DEĞİLDİR.
"""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GEXPlatform/1.0)"}
SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
NDX_URL = "https://en.wikipedia.org/wiki/List_of_NASDAQ-100_companies"
TARGET = Path(__file__).resolve().parent.parent / "data" / "universe.py"


def _tables(url: str) -> list[pd.DataFrame]:
    req = urllib.request.Request(url, headers=HEADERS)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    return pd.read_html(io.StringIO(html))


def fetch_universe() -> dict[str, dict]:
    out: dict[str, dict] = {}

    sp = next(t for t in _tables(SP500_URL) if "Symbol" in t.columns and "Security" in t.columns)
    for _, row in sp.iterrows():
        ticker = str(row["Symbol"]).strip().upper()
        out[ticker] = {
            "name": str(row["Security"]).strip(),
            "sector": str(row.get("GICS Sector", "")).strip(),
            "idx": ["SP500"],
        }

    for table in _tables(NDX_URL):
        cols = [str(c) for c in table.columns]
        tick_col = next((c for c in cols if c.strip() in ("Ticker", "Symbol")), None)
        if not tick_col or len(table) < 90:
            continue
        name_col = next((c for c in cols if "Comp" in c or "Name" in c), None) or cols[0]
        for _, row in table.iterrows():
            ticker = str(row[tick_col]).strip().upper()
            if not ticker or ticker == "NAN":
                continue
            if ticker in out:
                if "NDX" not in out[ticker]["idx"]:
                    out[ticker]["idx"].append("NDX")
            else:
                out[ticker] = {"name": str(row[name_col]).strip(), "sector": "", "idx": ["NDX"]}
        break

    return out


def write_module(data: dict[str, dict]) -> int:
    rows = []
    for ticker, v in sorted(data.items()):
        # Yahoo Finance hisse sınıfı ayıracı '-' kullanır (BRK.B -> BRK-B)
        rows.append(
            (
                ticker.replace(".", "-"),
                (v["name"] or "").replace('"', "'").strip(),
                (v["sector"] or "").replace('"', "'").strip(),
                "+".join(sorted(set(v["idx"]))),
            )
        )

    header = '''"""S&P 500 + NASDAQ-100 sembol evreni (statik).

Kaynak: Wikipedia (List_of_S&P_500_companies, List_of_NASDAQ-100_companies).
Çalışma anında ağa BAĞIMLI DEĞİLDİR; listeyi tazelemek için:
    python -m app.scripts.refresh_universe

Ticker'lar Yahoo Finance formatındadır (hisse sınıfı ayıracı '-', örn. BRK-B).
`index` alanı: SP500 | NDX | SP500+NDX
"""
from __future__ import annotations

# (ticker, şirket adı, sektör, endeks)
UNIVERSE: list[tuple[str, str, str, str]] = [
'''
    body = "".join(f'    ("{t}", "{n}", "{s}", "{i}"),\n' for t, n, s, i in rows)
    footer = ''']

SP500 = [t for t, _, _, i in UNIVERSE if "SP500" in i]
NDX = [t for t, _, _, i in UNIVERSE if "NDX" in i]
ALL_TICKERS = [t for t, _, _, _ in UNIVERSE]
'''
    TARGET.write_text(header + body + footer, encoding="utf-8")
    return len(rows)


def main() -> None:
    data = fetch_universe()
    count = write_module(data)
    print(f"{TARGET} güncellendi: {count} sembol")
    print("Veritabanına yansıtmak için: python -m app.seed")


if __name__ == "__main__":
    main()
