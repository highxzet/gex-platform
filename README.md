# GEX Analiz Platformu

Banka hisselerinin opsiyon zinciri verisinden **Net Gamma Exposure (GEX)** hesaplayan,
gamma flip / call wall / put wall seviyelerini çıkaran ve bir web arayüzünde sunan
full-stack platform.

- **Mühendislik spesifikasyonu:** `gex-platform-build-spec.md`
- **Tasarım:** `GEX Platformu.dc.html` (claude.ai/design) — ekranlar buna göre inşa edilir.

## Yapı
```
gex-platform/
├── gex-backend/      # FastAPI + PostgreSQL + Calculation Engine (Bölüm 6–9)
├── gex-frontend/     # React + TypeScript + Vite (Bölüm 10, 20)
├── docker-compose.yml
└── Caddyfile         # reverse proxy: / → frontend, /api → backend
```

## Hızlı başlangıç (geliştirme)

**Backend** (Python 3.11+, PostgreSQL):
```bash
cd gex-backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# → http://localhost:8000/health  ve  /docs
```

**Frontend** (Node 20+):
```bash
cd gex-frontend
npm install
cp .env.example .env
npm run dev
# → http://localhost:5173  (/api istekleri backend'e proxy'lenir)
```

**Hepsi birden (Docker):**
```bash
docker compose up --build
# → http://localhost  (Caddy proxy)
```

## Durum — Build Roadmap (Bölüm 19)
| Faz | Kapsam | Durum |
|---|---|---|
| 0 | Proje iskeleti (bootable backend + frontend) | ✅ bu commit |
| 1 | Veri modeli + Calculation Engine + %100 birim test | ⏳ sıradaki |
| 2–3 | Veri kaynağı + zamanlanmış iş + DB yazma | ⏳ |
| 4–5 | Kimlik doğrulama + temel API + ekranlar | ⏳ |
| 6–9 | Frontend ekranlarının tasarıma göre tamamlanması | ⏳ |

> Ekranlar, `GEX Platformu.dc.html` tasarım dosyası çekildikten sonra birebir inşa edilir.
> Şu anki frontend, koyu tema tasarım sistemini ve uygulama kabuğunu (sidebar + routing) içerir.
