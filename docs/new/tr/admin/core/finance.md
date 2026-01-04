# Finance (TR)

**Menü yolu (UI):** Core → Finance  
**Frontend route:** `/finance`  
**Sadece owner:** Evet (menu config)  

---

## 1) Amaç ve kapsam

Finance menüsü, tenant seviyesinde transaction izleme, mutabakat ve risk incelemesi için operatör görünümü sağlar. Bakiye uyuşmazlıklarını teşhis etmek, şüpheli işlemleri incelemek ve operasyonel finans akışlarını yönetmek için kullanılır.

---

## 2) Kim kullanır / yetki gereksinimi

- Öncelikle Platform Owner (super admin).
- Owner seviyesinde Finance/Ops roller.
- Tenant admin’lerin erişimi genellikle yoktur.

---

## 3) Alt başlıklar / sekmeler

Mevcut UI (`frontend/src/pages/Finance.jsx`):
- Overview summary kartları
- Transactions list
- Player risk/balance panelleri (build’e bağlı)

Backend yüzeyleri ayrık:
- Core finance transactions (`routes/core.py`): `GET /api/v1/finance/transactions`
- Advanced finance actions (`routes/finance.py`): `/api/v1/finance/*` altında withdrawal review

---

## 4) Temel akışlar (adım adım)

### 4.1 Transaction görüntüleme
1) Finance aç.
2) Filtreleri kullan (type/status/date range varsa).
3) Amount/state/player alanlarını incele.

**API çağrıları (observed/expected):**
- Liste: `GET /api/v1/finance/transactions?type=<...>&page=<n>&page_size=<n>`

### 4.2 Transaction üzerinden player inceleme
1) Satırdan `player_id` tespit et.
2) Players menüsüne gidip `player_id` ile ara.

### 4.3 Mutabakat görünümü (varsa)
- Bazı deploy’larda özet kartlar veya ayrı rapor olabilir.

---

## 5) Saha rehberi (pratik ipuçları)

- Mutlaka şu bilgileri kaydet:
  - transaction id
  - player id
  - tenant
  - time window
- Dispute’larda cross-check:
  - ledger değişimleri
  - withdrawal state
  - payout attempt’ler

**Yapmayın:**
- Break-glass olmadan manuel balance override.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** Finance sayfası “Network error” veriyor veya hiç yüklenmiyor.
   - **Muhtemel neden:** backend erişilemiyor veya auth invalid.
   - **Çözüm:** yeniden login; backend erişimi doğrula; DevTools Network kontrol.
   - **Doğrulama:** `GET /api/v1/finance/transactions` 200 döner.

2) **Semptom:** Transactions listesi boş.
   - **Muhtemel neden:** time window/filtre çok dar; tenant context yanlış.
   - **Çözüm:** filtreleri genişlet; tenant context doğrula.
   - **Doğrulama:** liste endpoint’i item döner.

3) **Semptom:** Oyuncu bakiye uyuşmazlığı bildiriyor.
   - **Muhtemel neden:** pending withdrawal held bakiye; geciken ledger reconciliation.
   - **Çözüm:** withdrawal state kontrol; ledger balance endpoint’i varsa kontrol et.
   - **Doğrulama:** wallet ledger available/held beklenen gibi.

4) **Semptom:** Finance ile Reports toplamları farklı.
   - **Muhtemel neden:** timezone/aggregation farkı; report caching.
   - **Çözüm:** aynı period boundary/timezone ile karşılaştır; raporu yeniden üret.
   - **Doğrulama:** tutarlar beklenen toleransta.

5) **Semptom:** Transaction’a tıklayınca 404.
   - **Muhtemel neden:** transaction detail endpoint yok.
   - **Çözüm:** listeden alanlarla çalış; detail gerekiyorsa backend’e escalate.
   - **Doğrulama:** detail endpoint 200 döner (implement edilirse).

6) **Semptom:** Yavaş yükleniyor / timeout.
   - **Muhtemel neden:** geniş date range.
   - **Çözüm:** aralığı daralt; page size düşür.
   - **Doğrulama:** response süresi iyileşir.

7) **Semptom:** 403 Forbidden.
   - **Muhtemel neden:** platform owner değil / yetki yok.
   - **Çözüm:** owner admin ile dene; rol doğrula.
   - **Doğrulama:** doğru role ile çağrılar başarılı.

8) **Semptom:** Export yok.
   - **Muhtemel neden:** export bu build’de yok.
   - **Çözüm:** Reports export’u kullan (varsa).
   - **Doğrulama:** Reports’ta export dosyası üretilir.

9) **Semptom:** Transaction status tutarsız görünüyor.
   - **Muhtemel neden:** async payout processing; state machine transition.
   - **Çözüm:** payout attempt ve withdrawal review geçmişini kontrol et.
   - **Doğrulama:** state geçişleri beklenen patikada.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Semptom:** Transaction detail / drill-down aksiyonları 404 dönüyor.
   - **Muhtemel neden:** UI detail endpoint çağırıyor; backend’de route yok.
   - **Impact:** Admin transaction detail ekranına inemez; list verisiyle çalışır.
   - **Admin Workaround:** List alanları + player detail + withdrawal audit ile inceleme yap.
   - **Escalation Package:**
     - Method + path: DevTools’tan al
     - Request sample: cURL export
     - Expected vs actual: expected 200, actual 404
     - Log: `finance` + tx id ile ara
   - **Resolution Owner:** Backend
   - **Verification:** Detail route 200 döner ve UI drill-down çalışır.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Transactions listesi yüklenir ve filtreler çalışır.

### 8.2 System → Logs
- Finance endpoint error’larına bak.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `finance/transactions`
  - `TX_NOT_FOUND`
  - `tenant_id`

### 8.4 System → Audit Log
- Beklenen event’ler (varsa): finance aksiyonları, withdrawal review.

### 8.5 DB audit (varsa)
- Ground truth: `transaction` tablosu.
- `auditevent` finance aksiyonlarını içermeli.

---

## 9) Güvenlik notları + geri dönüş

- Finance aksiyonları yüksek etkili olabilir.
- Audit dışı balance değişimi yapılmaz.

---

## 10) İlgili linkler

- Withdrawals: `/docs/new/tr/admin/core/withdrawals.md`
- Reports: `/docs/new/tr/admin/system/reports.md`
- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
