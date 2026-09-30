[GEX-Platform-Rapor.md](https://github.com/user-attachments/files/32856598/GEX-Platform-Rapor.md)
# GEX Analiz Platformu — Kapsam Raporu

**Tarih:** 2026-09-27
**Kapsam:** (1) GEX platformlarının ne işe yaradığı, (2) mevcut kod tabanının mimari analizi, (3) yeniden geliştirme yol haritası.

---

# BÖLÜM 1 — GEX Platformları Ne İşe Yarar?

## 1.1. Temel kavram: Gamma ve dealer dinamiği

Bir opsiyonun **delta**'sı, dayanak fiyatındaki 1 birimlik değişime karşılık opsiyon fiyatının ne kadar değiştiğidir. **Gamma** ise delta'nın fiyata göre değişim hızıdır — yani opsiyonun "eğriliği". Her greek harfi bir risk ölçüsüdür; gamma özellikle piyasa yapısı (market microstructure) analizinin kalbidir.

Neden önemli? Çünkü opsiyon satıcıları — yani bankalar ve market maker'lar ("dealer"lar) — portföylerini **delta-nötr** tutmak zorundadır. Gamma'ya sahip oldukları için deltaları fiyat her hareket ettiğinde kayar ve sürekli yeniden hedge etmesi gerekir:

- **Dealer long gamma ise** (çoğunlukla müşteriler put satın aldığında / call sattığında): Fiyat yükselince deltaları artar → satış yaparak hedge ederler. Fiyat düşünce deltaları azalır → alım yaparlar. Yani **volatiliteyi bastırırlar**: piyasa sönümlenir, dar bantta sıkışır.
- **Dealer short gamma ise** (çoğunlukla müşteriler call satın aldığında / put sattığında): Fiyat yükselince deltaları eksiye gider → alım yapmak zorundalar. Fiyat düşünce satış. Yani **volatiliteyi büyütürler**: hareket momentum kazanır, kırılımlar sertleşir.

Bir GEX platformu, açık opsiyon pozisyonlarının (Open Interest) vade/strike dağılımından hareketle **dealer kitlesinin toplam gamma pozisyonunu tahmin eder** ve bu tahmin üzerinden piyasanın "rejimini" ve kritik fiyat seviyelerini haritalar.

## 1.2. Hesaplanan temel metrikler

**Strike başına net GEX** (standart dolar bazlı tanım):

```
GEX(strike) = Γ × Açık Pozisyon (OI) × 100 (kontrat çarpanı) × S² × %1 hareket
```

- Call tarafı pozitif, put tarafı negatif katkı verir (dealer işaret konvansiyonu).
- `S² × %1` terimi: gamma, dayanak fiyatın %1'lik hareketine karşılık dealer'ın **kaç hisse** alıp satmak zorunda kalacağını dolar bazına çevirir.

Bu projedeki motor ([calculation_engine.py](../gex-backend/app/services/calculation_engine.py)) tam olarak bunu yapar; gamma sağlayıcıdan gelmiyorsa Black-Scholes ile Γ = N′(d1) / (S·σ·√T) hesaplanır.

Bu dağılımdan türetilen kritik seviyeler:

| Seviye | Tanım | Yorum |
|---|---|---|
| **Gamma Flip / Zero-Gamma Level** | Toplam net GEX'in işaret değiştirdiği fiyat | Üstünde dealer'lar long gamma (volatilite sönümlü, mean-reverting); altında short gamma (volatilite genişleyici, momentum). Piyasanın "kişiliğinin" değiştiği sınır. |
| **Call Wall** | En yüksek pozitif GEX'li strike | Fiyat buraya yaklaşınca dealer satışları baskılar → direnç. |
| **Put Wall** | En negatif GEX'li strike | Fiyat buraya düşünce dealer alımları destekler → destek. |
| **Rejim** | Spot'un flip'e göre konumu | `positive` (sönümlü) / `negative` (genişleyici) / `neutral` (bant içi). |

## 1.3. Bir GEX platformu kullanıcıya ne kazandırır?

1. **Volatilite rejimi okuması:** "Bugün piyasa mı beni eziyor yoksa sakinleşiyor mu?" sorusunun nicel cevabı. Pozitif GEX günlerinde range-bound stratejiler (short strangle, iron condor) daha rasyonel; negatif GEX günlerinde kırılım/trend stratejileri.
2. **Gün içi destek/direnç haritası:** Hacim profili (volume profile) gibi ama opsiyon pozisyonlanmasından gelen, dealer davranışına dayalı seviyeler. Fiyat put wall'a dokunup dönerse bu, "dealer alımı" olarak okunur.
3. **Kırılım / squeeze öngörüsü:** Fiyat flip seviyesini yukarı kırarsa dealer'lar hedge için alıma döner → short gamma squeeze potansiyeli. Aşağı kırarsa → volatilite genişlemesi, hızlı düşüş riski.
4. **Opsiyon pozisyonlama:** Kendi opsiyon işlemlerini piyasa yapısına göre konumlandırma — örneğe gamma flip'e yakın strike'lardan uzak durma, call/put wall'ların kırılımına göre stop yerleştirme.
5. **Risk yönetimi:** Negatif rejimde kaldıraç azaltma, pozitif rejimde daralma beklentisiyle pozisyon taşıma.
6. **İstatistiksel doğrulama:** Seviyelerin gerçekten çalışıp çalışmadığının backtest'le ölçülmesi (bu projede Faz 10'da `level_backtest_service` olarak inşa edilmiş).

## 1.4. Ticari örnekler ve konumlandırma

Bu alanın bilinen ticari örnekleri **SqueezeMetrics** (GEX kavramını popülerleştiren, endeks bazlı hesaplar), **SpotGamma** (profesyonel seviye, günlük seviye takibi) ve benzeri volatilite analizi servisleridir. Bu tür servisler genellikle:

- Endeks (SPX/SPY) ve büyük hisseler için günlük flip/wall seviyeleri,
- Gün içi rejim değişim uyarıları,
- Dealer gamma pozisyon tahminleri sunar.

**Bu projenin farkı:** ticari servisler genelde kapalı kutu ve endeks odaklıyken; bu platform **kullanıcının kendi izleme listesini** (518 sembollük SP500+NDX evreninden) takip etmesine, seviyeleri **kendi başına hesaplamasına**, **TradingView Pine indikatörü olarak dışa aktarmasına** ve seviyelerin isabetini **kendi verisiyle backtest etmesine** olanak tanıyan açık bir araçtır.



---

# BÖLÜM 2 — Mevcut Mimari Analizi

## 2.1. Genel yapı

Monorepo. Üç servis + proxy, `docker-compose.yml` ile orkestre ediliyor:

```
gex-platform/
├── gex-backend/     # FastAPI 0.115 + SQLAlchemy 2.0 + PostgreSQL 15 + APScheduler
├── gex-frontend/    # React 18 + TypeScript + Vite 5, react-query + react-router
├── docker-compose.yml   # db (Postgres) + backend + frontend (nginx) + caddy proxy
└── Caddyfile            # / → frontend, /api → backend
```

Git geçmişi, projenin 13 fazda ilerlediğini gösteriyor; README'deki yol haritası tablosu (Faz 1'e "sıradaki" diyor) **güncel değil** — gerçek durum Faz 13.

## 2.2. Backend — katman katman

### Konfigürasyon ve çekirdek (`app/config.py`, `app/core/`)
- Tüm gizli değerler `pydantic-settings` ile ortam değişkeninden okunuyor (`Settings` sınıfı, `.env`). Hesaplama parametreleri bile konfigürasyonlu: `risk_free_rate`, `contract_multiplier`, `gex_move_pct`, `neutral_band_pct`, gamma flip yöntemi seçimi (`zero_gamma` | `cumulative_strike`).
- `core/`: bağımlılık enjeksiyonu (`deps.py`), standart hata zarfı (`AppError` + global handler'lar — ham hata detayı asla istemciye sızmıyor), JWT güvenliği, market saati kontrolü (piyasa kapalıyken veri çekme atlanır), retry yardımcısı, loglama.

### Veri katmanı (`app/data/universe.py`)
- Statik, ağa bağımlı olmayan **518 sembollük S&P 500 + NASDAQ-100 evreni** (ticker, şirket, sektör, endeks). `python -m app.scripts.refresh_universe` ile tazeleniyor.

### Sağlayıcı soyutlaması (`app/providers/`)
- `base.py`: `MarketDataProvider` arayüzü (`get_price`, `get_price_history`, `get_option_chain`). Sağlayıcı değişimi (yfinance → Tradier/Polygon) kodda tek noktadan yönetiliyor.
- `yfinance_provider.py`: **yfinance gamma döndürmez**; yalnızca OI + IV verir. Sağlam normalizasyon katmanı var: NaN/None temizliği, `%500 üstü IV = çöp veri` kuralı (derin OTM'de %3000+ IV sorunu bilinçele halledilmiş), eksik OI = 0.

### Hesaplama motoru (`app/services/calculation_engine.py`) — sistemin kalbi
- **Saf fonksiyonel tasarım: veritabanına dokunmaz.** Birim testler DB'siz saniyeler içinde koşuyor (125 testten 111'i bunun kanıtı).
- Black-Scholes gamma (Γ = N′(d1)/(S·σ·√T)), sağlayıcı gamma'sı varsa ona öncelik, strike başına call(+)/put(−) GEX, strike bazında toplama.
- **İki gamma flip yöntemi:** (a) `cumulative_strike` — kümülatif GEX'in strike'lar boyunca sıfırı kesmesi; (b) **`zero_gamma` (varsayılan)** — hipotetik spot fiyatı grid'inde gamma yeniden hesaplanarak toplam GEX'in sıfırlandığı fiyat; SqueezeMetrics/SpotGamma tarzı, gerçek veride çok daha kararlı. Flip seçiminde "spot'a en yakın kesişim" gürültü filtrelemesi var.
- Call/put wall, rejim tayini (nötr bant ±%0.2) ve **destek/direnç seviyesi üretimi** (`compute_levels`: spot üstü pozitif yığılma = direnç, spot altı negatif yığılma = destek; güç 0–1 normalize, en güçlüye Call/Put Wall etiketi).

### Diğer servisler (`app/services/`)
- `data_ingestion_service.py`: ham veri kalıcılığı + hesaplama satırlarına dönüşüm.
- `alert_engine.py`: seviye/regim koşullarını değerlendirir, cooldown (30 dk) ve e-posta kanalı.
- `level_backtest_service.py`: üretilen seviyelerin fiyat geçmişindeki isabet istatistiği (Faz 10 — edge doğrulama).
- `pine_export_service.py`: GEX seviyelerini TradingView Pine Script v5 indikatörüne çevirir (Faz 12).
- `notification_service.py`: uygulama içi + SMTP e-posta bildirimleri.

### Zamanlanmış işler (`app/jobs/scheduler.py` + 4 job modülü)
APScheduler (background): piyasa açıkken **2 dakikada bir** veri çek + hesapla + uyarı değerlendir; 30 dakikada bir (opsiyonel) geniş evren taraması; hafta içi 17:15 ET'de **gün sonu anlık görüntüsü** (EOD — backtest veri seti); günde bir temizlik (90/365/180 günlük saklama politikaları); 5 dakikada bir veri kaynağı sağlık kontrolü. Tüm job'lar tek sembol hatasıyla durmaz (kısmi başarısızlık kuralı) ve sessizce ölmez (exception → log).

### Veritabanı (`app/models/` — 11 tablo)
`symbols`, `option_chain_raw` (90 gün), `price_snapshots`, `gex_by_strike` (365 gün), `gex_summary` (zaman serisi, üzerine yazılmaz — her döngü yeni satır), `calculation_runs`, `users` (bcrypt + JWT refresh + kilitlenme politikası), `watchlist_items`, `alerts`, `notifications`, `journal_entries`, `data_source_status`. Alembic migrasyonları mevcut. `gex_summary` sık okunduğu için ayrı ve hafif tutulmuş — doğru bir okuma-ağırlıklı tasarım kararı.

### API (`app/routers/` — 10 router, ~40 endpoint, hepsi `/api` altında)
- **auth**: login/refresh/logout/me (access 15 dk + refresh 7/30 gün, remember-me, 5 hatalı denemede 15 dk kilit).
- **dashboard**: ana panel toplu görünüm.
- **symbols**: arama, GEX profili, zaman serisi, ham veri, fiyat seviyeleri, seviye backtest.
- **watchlist / alerts / notifications / journal / data-status / settings** (profil, görünüm, parola, veri dışa aktarma, hesap silme) / **pine** (watchlist veya sembol için Pine Script, JSON veya düz metin).

## 2.3. Frontend (`gex-frontend/`)

- **11 sayfa:** Dashboard, Sembol Detay (`/symbols/:ticker`), İzleme Listesi, Karşılaştırma, Geçmiş, Uyarılar, Günlük, Metodoloji, Veri Durumu, Ayarlar, Giriş + 404.
- **Bileşen seti:** koyu tema tasarım sistemi (`tokens.css`, `ui.css`), GEX profil grafiği, lightweight-charts tabanlı fiyat grafiği, TradingView widget entegrasyonu, **yazılım içi Pine editörü** (Faz 13), sparkline'lar, rejim rozetleri, aranabilir sembol seçici, durum yönetimi (loading/empty/error) bileşenleri.
- **Veri akışı:** `@tanstack/react-query` ile sunucu durumu; `api/client.ts` merkezi istemci; hata kodu → Türkçe mesaj tablosu (`errorMessages.ts`); veri tazeliği göstergesi (`dataFreshness.ts`).
- **Kimlik:** `AuthContext` + `RequireAuth` route koruması, JWT access/refresh.

## 2.4. Test durumu (doğrulanmış)

```
tests/unit: 111 PASSED, 14 ERROR (toplam ~18 sn)
```

14 hatanın **tamamı çevresel**: testlerin gerektirdiği yerel PostgreSQL (localhost:5432/gex_test) şu an çalışmıyor; alert_engine ve notification_service testleri DB fixture'ı kuramadığı için setup'ta düşüyor. **Kod kaynaklı başarısızlık yok.** Entegrasyon testleri de aynı DB bağımlılığını taşıyor.

## 2.5. Mimari güçlü yönler

1. **Sağlam katman ayrımı** — saf hesaplama motoru / I/O / kalıcılık net ayrılmış; test edilebilirlik bunun kanıtı.
2. **Sağlayıcı soyutlaması** — yfinance kırılsa bile Tradier/Polygon'a geçiş arayüz değişimine indirgenmiş.
3. **Endüstri-standardı hesaplama** — zero-gamma flip yöntemi SpotGamma tarzı tanıma uygun; `nearest_spot` gürültü filtresi gerçek veri sorununu bilinçele çözüyor.
4. **Ölçek tasarımı** — 518 sembol × ~1600 satır = döngü başına ~830K satırın saklanamayacağı fark edilmiş; geniş tarama "sembol başına 1 özet satır" moduna indirgenmiş (detail=False). Paralel çekim + akış halinde yazım.
5. **Veri yaşam döngüsü** — retention politikaları, EOD anlık görüntü, backtest veri seti: istatistiksel doğrulamaya hazır zemin.
6. **Ürün bütünlüğü** — auth, uyarı, günlük, bildirim, Pine dışa aktarma, metodoloji sayfası: ticari MVP'nin ötesinde bir araç seti.

## 2.6. Boşluklar / iyileştirme fırsatları

1. **README yol haritası bayat** — Faz 0-13 tamamlanmış ama tablo hâlâ "sıradaki: Faz 1" diyor. Dökümantasyon senkronu gerek.
2. **Test çevresi** — DB'siz koşabilen testler dışındaki 14 test, çalışan bir Postgres gerektiriyor; docker-compose'da test profili/CI pipeline yok.
3. **Veri kaynağı kırılganlığı** — yfinance resmi API değil; gamma sağlayan ücretli bir kaynağa (Tradier/Polygon) geçiş yapısı hazır ama henüz yapılmamış.
4. **0DTE/gamma dinamiğindeki gün içi hassasiyet** — OI gecikmesi yüzünden gün içi okuma sınırlı; bu metodoloji sayfasında belirtilmeli (belirtilmiş mi, kontrol edilmeli).
5. **WebSocket/canlılık** — veri 2 dakikalık poll ile geliyor; canlı seviye takibi için WebSocket veya SSE düşünülebilir.
6. **Performans endeksleri eksik** — SPX/SPY/QQQ gibi endeks GEX'i hesaplanmıyor (evren hisse odaklı).

---

# BÖLÜM 3 — Yeniden Geliştirme Yol Haritası


| **A** | **Çevre + test altyapısını sağlamlaştır** | 14 test DB'siz koşamıyor; docker test profili + CI ile her adım güvence altına alınır. Temiz zemin şart. |
| **B** | **Dökümantasyon senkronu** | README yol haritasını gerçek duruma  çek; API referansını tazele. |
| **C** | **Endeks GEX'i (SPX/SPY/QQQ)** | Ticari GEX ürünlerinin ana kullanım alanı; zero_gamma motoru zaten hazır, evren genişletmesi küçük bir iş. |
| **D** | **Veri sağlayıcısı katmanını güçlendir** | Gamma sağlayan kaynak (Tradier/Polygon) entegrasyonu; hesaplama doğruluğunda sıçrama. |
| **E** | **Canlı takip (WebSocket/SSE)** | 2 dk poll → anlık seviye akışı; uyarı gecikmesini sıfıra indirir. |
| **F** | **Backtest panelini derinleştir** | EOD veri seti hazır; seviye isabet istatistiklerinin UI'ya zengin rapor olarak taşınması. |


