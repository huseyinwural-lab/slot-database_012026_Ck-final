# API Keys (TR)

**Menü yolu (UI):** System → API Keys  
**Frontend route:** `/keys`  
**Sadece owner:** Evet  

---

## 1) Amaç ve kapsam

API Keys menüsü, external entegrasyonlar ve internal otomasyonlar (örn. Game Robot) için scope-based API key yönetimini sağlar. Key’ler **kritik güvenlik secret**’larıdır.

---

## 2) Kim kullanır / yetki gereksinimi

- Sadece Platform Owner (super admin).
- Tenant admin’lerin API key yönetimine erişimi olmamalıdır.

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI’da (`frontend/src/pages/APIKeysPage.jsx`):
- Key list
- Create key (dialog)
- Active/Inactive toggle
- Scopes seçimi

---

## 4) Temel akışlar

### 4.1 Key listesini görüntüleme
1) System → API Keys aç.
2) Mevcut key’leri incele:
   - Name
   - Key prefix
   - Tenant
   - Scopes
   - Status

**API çağrıları (frontend’den gözlemlendi):**
- Liste: `GET /api/v1/api-keys/`
- Scope kataloğu: `GET /api/v1/api-keys/scopes`

### 4.2 Yeni API key oluşturma
1) **New API Key** tıkla.
2) **Name** gir (net bir naming standardı kullan).
3) **Scopes** seç (least privilege).
4) **Create**.
5) Üretilen secret’ı kopyala.

**Önemli:** secret **sadece bir kez** gösterilir.

**API çağrıları (frontend’den gözlemlendi):**
- Create: `POST /api/v1/api-keys/` body `{ name, scopes }`

### 4.3 API key rotation (önerilen prosedür)
Rotation, UI’da özel bir “rotate” butonu olmasa bile operasyonel bir pattern’dir (eski+yeni paralel).

1) Aynı scope’larla **yeni key** oluştur.
2) Entegrasyon config’ini **yeni key** ile deploy et.
3) Başarılı istekleri doğrula.
4) Eski key’i disable/revoke et.

### 4.4 Key revoke/disable
Mevcut UI’da disable işlemi Active/Inactive toggle ile yapılır.

**API çağrıları (frontend’den gözlemlendi):**
- Active toggle: `PATCH /api/v1/api-keys/{id}` body `{ active: true|false }`

**Önemli implementasyon notu:** Mevcut backend route’larında `PATCH /api/v1/api-keys/{id}` endpoint’i yok. Bu build’de UI toggle sırasında **404 Not Found** alabilir.

---

## 5) Saha rehberi (pratik ipuçları)

- Naming standardı önerisi: `<system>-<env>-<purpose>-<owner>-<date>`.
- En küçük scope setini seç (least privilege).
- Secret’ları secret manager’da sakla (ticket/chat/screenshot’ta paylaşma).
- Incident sırasında API key’leri “kompromize olabilir” varsayımıyla yönet.

**Yapmayın:**
- Prod key’i staging’de kullanma.
- “Geçici” key’leri uzun süre aktif bırakma.

---

## 6) Olası hatalar (semptom → muhtemel neden → çözüm → doğrulama)

> Minimum 8 madde (güvenlik/incident yüzeyi).

1) **Semptom:** Entegrasyonda 401 Unauthorized
   - Muhtemel neden: yanlış key, typo, `Authorization` header eksik.
   - Çözüm: doğru secret kullanıldığını doğrula; secret store’dan yeniden çek.
   - Doğrulama: backend log’larında başarılı auth; istekler 200 döner.

2) **Semptom:** 403 Forbidden
   - Muhtemel neden: scope yetersiz.
   - Çözüm: doğru scope’larla yeni key oluştur (least privilege).
   - Doğrulama: yeni key’e geçince istek başarılı.

3) **Semptom:** UI’da “Failed to load API key data”
   - Muhtemel neden: `/api/v1/api-keys/` çağrısı fail veya tenant feature disabled.
   - Çözüm: platform owner yetkisini doğrula; Network response/error code kontrol et.
   - Doğrulama: key list + scopes list yüklenir.

4) **Semptom:** “Failed to create API key”
   - Muhtemel neden: name yok; scope seçilmedi; invalid scope.
   - Çözüm: name gir; en az bir scope seç; tekrar dene.
   - Doğrulama: create çağrısı success ve secret bir kez gösterilir.

5) **Semptom:** Key oluştu ama secret kopyalanmadı
   - Muhtemel neden: dialog kapatıldı; secret sadece bir kez gösterilir.
   - Çözüm: yeni key oluştur; eskisini revoke/disable et (secret geri alınamaz).
   - Doğrulama: entegrasyon yeni secret ile çalışır; eski key inaktif.

6) **Semptom:** Active/Inactive toggle 404 döndürüyor
   - Muhtemel neden: backend `PATCH /api/v1/api-keys/{id}` implement edilmemiş.
   - Çözüm: backend versiyonunu doğrula; yoksa key’leri “create-only” kabul edip rotation’ı yeni key ile yap.
   - Doğrulama: backend güncellenince toggle çalışır veya yeni key ile akış tamamlanır.

7) **Semptom:** Rotation sonrası prod entegrasyon bozuldu
   - Muhtemel neden: config eski key’i kullanıyor; deploy uygulanmadı.
   - Çözüm: config change’i deploy et; gerekirse geçici olarak eski key’i re-enable et.
   - Doğrulama: başarılı istekler görülür, error rate düşer.

8) **Semptom:** Key leak şüphesi
   - Muhtemel neden: key plain text paylaşıldı/commit edildi/loglandı.
   - Çözüm: key’i hemen revoke/disable et; rotate et; incident prosedürü uygula.
   - Doğrulama: audit kanıtı + log’lar key’in revoke edildiğini ve trafiğin bloklandığını gösterir.

9) **Semptom:** Stage/prod karıştı
   - Muhtemel neden: staging key prod’da veya prod key staging’de.
   - Çözüm: environment sınırlarını doğrula; ayrı key’ler ve naming kullan.
   - Doğrulama: doğru environment’a istek atılır ve başarılıdır.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Active/Inactive toggle 404 Not Found dönüyor.
   - **Likely Cause:** UI `PATCH /api/v1/api-keys/{id}` çağırıyor; bu backend build’de key status update için PATCH route yok.
   - **Impact:** Admin UI üzerinden key disable/revoke edemez (güvenlik/incident response etkisi). Rotation “yeni key yarat + cutover” şeklinde yapılır.
   - **Admin Workaround:**
     - Doğru scope’larla yeni key oluştur.
     - Entegrasyon config’ini yeni key’e geçir.
     - Eski key’leri backend status update gelene kadar UI’dan disable edilemez kabul et.
   - **Escalation Package:**
     - HTTP method + path: `PATCH /api/v1/api-keys/{id}`
     - Request sample: `{ "active": false }`
     - Expected vs actual: expected 200; actual 404
     - Log keyword’leri:
       - `api-keys`
       - `PATCH`
       - `404`
   - **Resolution Owner:** Backend
   - **Verification:** Fix sonrası toggle 200 döner; key status değişimi refresh sonrası kalıcı.

---

## 8) Doğrulama (UI + Log + Audit + DB)

1) Hata veren endpoint’i ve error code’u (401/403/5xx) tespit et.
2) Hangi key’in kullanıldığını (prefix varsa) doğrula.
3) Gerekli scope’ları ve atanmış scope’ları karşılaştır.
4) Rotate et (yeni key → deploy config → verify → disable eski key).
5) Audit-ready kanıt üret (ne değişti, ne zaman, kim yaptı).

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Yeni oluşturulan key listede görünür.
- Görünen scope’lar least-privilege hedefiyle uyumludur.

### 8.2 System → Logs
- Auth failure/timeout’ları incele.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `api-key`
  - `Unauthorized` / `Forbidden`
  - scope validation error

### 8.4 System → Audit Log
- Beklenen audit event’leri (implementasyona göre değişir):
  - `api_key.created`
  - `api_key.revoked` / `api_key.disabled`

### 8.5 DB audit (varsa)
- Kanonik tablo: `apikey` / `api_key` (implementasyona göre).
- Kanıt olarak:
  - create için yeni satır
  - revoke/disable için status değişimi (destekleniyorsa)

---

## 9) Güvenlik notları + geri dönüş

- API key’ler prod blast-radius taşır.
- Geri dönüş stratejisi:
  - Rotation downtime yaratırsa: (destekleniyorsa) önceki key’i geçici re-enable edip doğru config’i deploy et.
  - Stabilizasyon sonrası tekrar rotate et ve riskli key’leri revoke et.

---

## 10) İlgili linkler

- Break-glass: `/docs/new/tr/runbooks/break-glass.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
