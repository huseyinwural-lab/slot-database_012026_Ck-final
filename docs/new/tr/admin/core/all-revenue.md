# All Revenue (TR)

**Menü yolu (UI):** Core → All Revenue  
**Frontend route:** `/owner-revenue`  
**Sadece owner:** Evet  

---

## 1) Amaç ve kapsam

All Revenue, tüm tenant’lar için platform-wide revenue analitiği sunar (GGR, bets, wins, transactions) ve belirli bir zaman aralığında yüksek seviye görünürlük sağlar. Platform owner’lar için oversight, anomaly detection ve üst seviye mutabakat amaçlıdır.

---

## 2) Kim kullanır / yetki gereksinimi

- Sadece Platform Owner (super admin).

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI (`frontend/src/pages/OwnerRevenue.jsx`):
- Date range seçici
- Tenant filter (All tenants veya tek tenant)
- Summary kartları
- Tenant bazlı breakdown tablosu

---

## 4) Temel akışlar (adım adım)

### 4.1 Date range değiştirme
1) Date range seç (24h / 7d / 30d / 90d).
2) Totallerin güncellendiğini gözle.

### 4.2 Tek tenant’a filtreleme
1) Tenant dropdown’dan tenant seç.
2) Totalleri ve satırı incele.

**API çağrıları (frontend’den gözlemlendi):**
- Revenue (all tenants): `GET /api/v1/reports/revenue/all-tenants?from_date=<iso>&to_date=<iso>&tenant_id=<optional>`

---

## 5) Saha rehberi (pratik ipuçları)

- Seçilen time window ve timezone varsayımını mutlaka not alın.
- Anomali doğrulamak için tenant filter kullanın.
- Detay mutabakat için Finance ve Reports ile cross-check yapın.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** “Failed to load revenue data” görünüyor.
   - **Muhtemel neden:** endpoint 404/500 veya auth sorunu.
   - **Çözüm:** platform owner rolünü doğrula; DevTools Network response kontrol.
   - **Doğrulama:** revenue endpoint 200 döner ve JSON total içerir.

2) **Semptom:** Değerler hep 0.
   - **Muhtemel neden:** aralıkta veri yok; tenant filter yanlış.
   - **Çözüm:** aralığı genişlet; All tenants seç.
   - **Doğrulama:** aralık genişleyince total değişir.

3) **Semptom:** Tenant dropdown boş.
   - **Muhtemel neden:** revenue payload tenants array boş.
   - **Çözüm:** tenant’ların varlığını Tenants ekranından doğrula.
   - **Doğrulama:** revenue response tenants array içerir.

4) **Semptom:** Finance ile toplamlar uyuşmuyor.
   - **Muhtemel neden:** aggregation tanımı veya timezone farkı.
   - **Çözüm:** aynı period boundary; timezone doğrula.
   - **Doğrulama:** beklenen toleransta reconcile.

5) **Semptom:** Yavaş yükleniyor.
   - **Muhtemel neden:** geniş aralık aggregation.
   - **Çözüm:** aralığı küçült; düşük trafikte çalıştır.
   - **Doğrulama:** response süresi düşer.

6) **Semptom:** Tenant seçince değerler değişmiyor.
   - **Muhtemel neden:** UI tenant_id paramını geçmiyor veya backend tenant_id’yi ignore ediyor.
   - **Çözüm:** request params kontrol; ignore ediliyorsa backend’e escalate.
   - **Doğrulama:** tenant seçimi total değiştirir.

7) **Semptom:** Beklenmeyen negatif GGR.
   - **Muhtemel neden:** data anomaly, refund/chargeback.
   - **Çözüm:** Finance transaction’larına in; chargeback kontrol.
   - **Doğrulama:** alttaki işlemler sonucu açıklar.

8) **Semptom:** 403 Forbidden.
   - **Muhtemel neden:** platform owner değil.
   - **Çözüm:** platform owner admin kullan.
   - **Doğrulama:** doğru role ile çağrı başarılı.

9) **Semptom:** Cache/stale revenue.
   - **Muhtemel neden:** cached summary.
   - **Çözüm:** refresh; daha sonra tekrar dene.
   - **Doğrulama:** `from_date/to_date` değişince değerler güncellenir.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Semptom:** Revenue endpoint 404 Not Found.
   - **Muhtemel neden:** backend’de `/api/v1/reports/revenue/all-tenants` route yok.
   - **Impact:** Platform-wide revenue ekranı bloklanır.
   - **Admin Workaround:** No admin-side workaround. Geçici olarak Finance + tenant-level revenue kullanılabilir.
   - **Escalation Package:**
     - Method + path: `GET /api/v1/reports/revenue/all-tenants`
     - Request sample: query params `from_date`, `to_date`, opsiyonel `tenant_id`
     - Expected vs actual: expected 200; actual 404
     - Log: backend log’larda `revenue` / `reports/revenue` ara
   - **Resolution Owner:** Backend
   - **Verification:** endpoint 200 döner ve UI total’leri render eder.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Date range değişince totaller değişir.
- Tenant filter totalleri değiştirir.

### 8.2 System → Logs
- Revenue endpoint 4xx/5xx var mı bak.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `reports/revenue`
  - `tenant_id`

### 8.4 System → Audit Log
- Genelde read-only; audit event beklenmeyebilir.

### 8.5 DB audit (varsa)
- Aggregation `transaction` tablosu ile reconcile edilebilir olmalı.

---

## 9) Güvenlik notları + geri dönüş

- Revenue ekranları hassas KPI içerir.
- Sadece platform owner erişimine izin ver.

---

## 10) İlgili linkler

- Finance: `/docs/new/tr/admin/core/finance.md`
- Reports: `/docs/new/tr/admin/system/reports.md`
- Tenants: `/docs/new/tr/admin/system/tenants.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
