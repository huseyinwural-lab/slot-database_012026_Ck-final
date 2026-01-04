# Reports (TR)

**Menü yolu (UI):** System → Reports  
**Frontend route:** `/reports`  
**Sadece owner:** Karışık (tenant feature `can_view_reports`’a bağlı)  

---

## 1) Amaç ve kapsam

Reports, operasyonel ve finansal agregasyon görünümleri sağlar (overview KPI’lar, tablolar, export). Karar destek, mutabakat ve kanıt üretimi için kullanılır.

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner: tenant context ve entitlement’a göre raporlara erişebilir.
- Tenant Admin / Finance: `can_view_reports` aktifse tenant raporlarını kullanır.
- Support/Risk: operasyonel/risk raporları kullanabilir.

---

## 3) Alt başlıklar / sekmeler

Mevcut UI’da (`frontend/src/pages/Reports.jsx`) navigation:
- Overview
- Real-Time (UI placeholder)
- Financial
- Players (LTV)
- Games
- Providers
- Bonuses
- Affiliates
- CRM
- CMS
- Operational
- Custom Builder (UI placeholder)
- Scheduled
- Export Center

Tab’a göre seçilen endpoint’ler:
- `GET /api/v1/reports/overview`
- `GET /api/v1/reports/financial`
- `GET /api/v1/reports/players/ltv`
- `GET /api/v1/reports/games`
- `GET /api/v1/reports/providers`
- `GET /api/v1/reports/bonuses`
- `GET /api/v1/reports/affiliates`
- `GET /api/v1/reports/risk`
- `GET /api/v1/reports/rg`
- `GET /api/v1/reports/kyc`
- `GET /api/v1/reports/crm`
- `GET /api/v1/reports/cms`
- `GET /api/v1/reports/operational`
- `GET /api/v1/reports/schedules`
- `GET /api/v1/reports/exports`

**Önemli implementasyon notu:** Backend’de `routes/reports.py` stub ve `routes/revenue.py` (kısmi) mevcut. Listelenen rapor endpoint’lerinin çoğu implement edilmemişse **404 Not Found** dönebilir.

---

## 4) Temel akışlar

### 4.1 Rapor görüntüleme
1) Reports aç.
2) Sol menüden rapor tipini seç.
3) Verinin yüklenmesini bekle.

**API çağrıları:**
- `GET /api/v1/reports/<tab-endpoint>`

### 4.2 Export
1) Rapor sekmesini seç.
2) **Export** tıkla.

**API çağrıları (frontend’den gözlemlendi):**
- Export job: `POST /api/v1/reports/exports` body `{ type, requested_by }`

### 4.3 Cross-check / doğrulama
- Finans raporlarını Finance ledger/transaction ile karşılaştır.
- Player raporlarını Players listesiyle karşılaştır.

---

## 5) Saha rehberi (pratik ipuçları)

- **Zaman aralığı** ve **timezone** mutlaka not alın.
- Timeout riskini azaltmak için küçük time range kullanın.
- Toplamlar tutarsızsa raporun:
  - cached snapshot mı
  - live aggregation mı
  olduğunu doğrulayın.

**Ne zaman kullanılmamalı:**
- Cross-check yapmadan “tek doğru kaynak” gibi kullanmak.

---

## 6) Olası hatalar (semptom → muhtemel neden → çözüm → doğrulama)

> Minimum 8 madde.

1) **Semptom:** Rapor boş geliyor
   - Muhtemel neden: filtre/time window; tenant context yanlış.
   - Çözüm: tarih aralığını genişlet; tenant context doğrula.
   - Doğrulama: endpoint rows döner ve UI tablo dolu.

2) **Semptom:** Rapor çok yavaş / timeout
   - Muhtemel neden: geniş time range; ağır aggregation.
   - Çözüm: time range küçült; düşük trafikte çalıştır.
   - Doğrulama: request süresi düşer ve tamamlanır.

3) **Semptom:** Export inmiyor
   - Muhtemel neden: browser download policy; export async.
   - Çözüm: Export Center sekmesini kontrol et; download izni ver.
   - Doğrulama: export dosyası görünür ve indirilebilir.

4) **Semptom:** Rapor toplamları Finance ile uyuşmuyor
   - Muhtemel neden: timezone; farklı tanım/aggregation; geciken ETL.
   - Çözüm: timezone doğrula; aynı period boundary ile karşılaştır; gecikme kontrolü.
   - Doğrulama: tutarlar beklenen toleransta.

5) **Semptom:** Duplicate satırlar
   - Muhtemel neden: aggregation bug veya grouping key.
   - Çözüm: raporu daralt; raw transaction ile karşılaştır.
   - Doğrulama: duplicate kaybolur veya grouping ile açıklanır.

6) **Semptom:** 403 Forbidden
   - Muhtemel neden: `can_view_reports` entitlement yok veya rol kısıtı.
   - Çözüm: tenant feature enable; role/permission doğrula.
   - Doğrulama: rapor tab’ı açılır.

7) **Semptom:** Rapor endpoint’leri 404 Not Found
   - Muhtemel neden: backend endpoint’leri bu build’de yok.
   - Çözüm: backend release versiyonunu doğrula.
   - Doğrulama: endpoint 200 döner ve veri gelir.

8) **Semptom:** Scheduled rapor gitmiyor
   - Muhtemel neden: scheduler/worker down; mailer yok.
   - Çözüm: job runner kontrol; mailer entegrasyon kontrol.
   - Doğrulama: schedule job log success ve output ulaşır.

9) **Semptom:** Cache/stale data
   - Muhtemel neden: report caching.
   - Çözüm: cache refresh veya raporu regenerate.
   - Doğrulama: “generated_at” değişir ve değerler güncellenir.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Rapor sekmelerinin çoğu 404 Not Found dönüyor.
   - **Likely Cause:** UI `/api/v1/reports/*` (overview/financial/...) endpoint’lerini çağırıyor; backend’de `routes/reports.py` stub durumda.
   - **Impact:** Reporting kısmen veya tamamen bloklanır (operasyonel izleme + kanıt üretimi etkilenir). Genelde preview/staging’de görülür; aynı build prod’a giderse prod’u da etkiler.
   - **Admin Workaround:** Geçici alternatif olarak kaynak menüleri kullan:
     - Finance (transactions/withdrawals)
     - Players
     - Games
     - Revenue sayfaları (varsa)
     Export endpoint yoksa: admin-side export workaround yok.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/reports/<tab>` (DevTools’tan net path alın)
     - Request sample: UI’ın gönderdiği query params
     - Expected vs actual: expected 200; actual 404
     - Log keyword’leri:
       - `reports`
       - endpoint path
       - `404`
   - **Resolution Owner:** Backend
   - **Verification:** Her sekmenin endpoint’i 200 döner ve UI tablo/kartlar dolu.

---

## 8) Çözüm adımları (adım adım)

1) Fail eden endpoint + status code al.
2) Tenant context ve entitlement doğrula.
3) Time window küçült.
4) Source menülerle cross-check (Finance/Players/Games).
5) Log/audit ile kanıt üret.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Tab içerikleri yüklenmeli.
- Export job oluşmalı ve Export Center’da görünmeli.

### 8.2 System → Logs
- Report request error’ları ve slow query’lere bak.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `reports`
  - `exports`
  - `timeout`

### 8.4 System → Audit Log
- Beklenen audit event (varsa):
  - `report.exported`
  - `report.generated`

### 8.5 DB audit (varsa)
- Tablo isimleri deploy’a göre değişir.
- Finans doğruluğu için ground truth: `transaction`/ledger tabloları.

---

## 9) Güvenlik notları + geri dönüş

- Raporlar hassas finansal ve kişisel veri içerebilir.
- Export dosyaları korunmalı ve erişimi time-bounded olmalıdır.
- Veri sızıntısında: erişimi kes, secret rotate et, audit kanıtı üret.

---

## 10) İlgili linkler

- Finance: `/docs/new/tr/admin/core/finance.md`
- Players: `/docs/new/tr/admin/core/players.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
