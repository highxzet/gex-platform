# GEX Backend 

Net Gamma Exposure (GEX) hesaplama ve izleme platformunun backend'i.
Mimari ve spesifikasyon: `gex-platform-build-spec.md` (Bölüm 6, 7, 8, 11).

## Gereksinimler
- Python 3.11+
- PostgreSQL 15+ (yerelde Docker ile ayağa kaldırılabilir — bkz. kök `docker-compose.yml`)

## Kurulum
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # değerleri doldur (özellikle JWT_SECRET_KEY, DATABASE_URL)
```

## Çalıştırma
```bash
uvicorn app.main:app --reload --port 8000
```
- Sağlık kontrolü: http://localhost:8000/health  → `{"status": "healthy"}`
- OpenAPI dokümanı: http://localhost:8000/docs

## Test
```bash
pytest tests/ -v
pytest tests/unit/ --cov=app.services.calculation_engine   # Faz 1 sonrası %100 hedef (Bölüm 13.7)
```

## Katmanlı mimari (Bölüm 6.1)
```
routers/  →  services/  →  repositories/  →  PostgreSQL
```
- `routers/`   HTTP giriş/çıkış (şu an skeleton stub'ları)
- `services/`  iş mantığı (calculation_engine, data_ingestion, alert_engine, auth)
- `providers/` veri kaynağı entegrasyonları (yfinance/tradier/polygon — Bölüm 4.3)
- `jobs/`      zamanlanmış işler (APScheduler — Bölüm 9)
- `models/`    SQLAlchemy ORM (Bölüm 5 — Faz 1)
- `schemas/`   Pydantic request/response (Bölüm 7)

## Yol haritası (Bölüm 19)
- **Faz 0 (bu skeleton):** app boot olur, `/health` çalışır. 
- **Faz 1:** modeller + `CalculationEngine` tam implementasyonu + %100 birim test.
- **Faz 2–3:** veri kaynağı entegrasyonu + zamanlanmış iş + DB yazma.
- **Faz 4–5:** kimlik doğrulama + temel API endpoint'leri.
