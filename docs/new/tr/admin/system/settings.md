# Ayarlar (Settings) (TR)

**Menü yolu (UI):** System → Settings  
**Frontend route:** `/settings`  
**Sadece owner:** Evet (menu config). Bazı aksiyonlar tenant-scope olabilir.  

---

## Ops Checklist (read first)

- Mutlaka **tenant context**i önce doğrula. Ayarlar değişiklikleri real-money akışlarını etkileyebilir.
- Her değişiklikte: request path + status code + response body al (DevTools → Network).
- Write aksiyonlarında (create/update/delete): mümkünse **Audit Log** ile kanıt topla.
- Yakında / placeholder tablara prodda güvenme.

---

## 1) Amaç ve kapsam

Settings, tenant/platform konfigurasyon yönetimi içindir: brand/tenant metadata, para birimleri, ülke kuralları (geoblocking/compliance), ödeme politikaları, API keyler ve varsayılanlar.

Bu menüde:
- **Çalışan tablar** (Brands, Currencies, Countries, Payments Policy, API Keys)
- **UI placeholder tablar** (Domains, Payment Providers, Games, Communication, Regulatory, Theme, Maintenance, Audit)

---

## 2) Kim kullanır / yetki gereksinimi

- Platform Owner (super admin)
- Bazı alt işlemler tenant adminlere açık olabilir (deploya göre).

> UI görünürlüğü: System  Settings menüsü `frontend/src/config/menu.js`de owner-only.

---

## 3) Alt başlıklar / tablar (UI)

`frontend/src/pages/SettingsPanel.jsx` tabları:

- Brands
- Domains (placeholder)
- Currencies
- Payment Providers (placeholder)
- Payments Policy
- Countries
- Games (placeholder)
- Communication (placeholder)
- Regulatory (placeholder)
- Defaults
- API Keys
- Theme (placeholder)
- Maintenance (placeholder)
- Versions (read-only)
- Audit (placeholder)

---

## 4) Temel akışlar (adım adım)

### 4.1 Brands (liste)
1) Settings  Brands tabını aç.
2) Liste yüklendi mi kontrol et.

**API çağrıları (frontendden gözlemlenen):**
- `GET /api/v1/settings/brands`

### 4.2 Brands (oluşturma)
1) **Add Brand** tıkla.
2) Doldur:
   - brand_name
   - default_currency
   - default_language
3) Submit.

**API çağrıları:**
- `POST /api/v1/settings/brands`

> Not: Backend response şekli UI beklentisiyle uyumlu olmalı (bkz. gap).

### 4.3 Currencies (create/edit/delete)
1) Settings  Currencies tabını aç.
2) Yeni Para Birimi ile create/edit yap.
3) Gerekirse (USD harici) delete.

**API çağrıları:**
- `GET /api/v1/settings/currencies`
- `POST /api/v1/settings/currencies`
- `PUT /api/v1/settings/currencies/{id}`
- `DELETE /api/v1/settings/currencies/{id}`

### 4.4 Countries (kuralları görüntüleme)
1) Settings  Countries tabını aç.
2) Country rules ve KYC levelı kontrol et.

**API çağrıları:**
- `GET /api/v1/settings/country-rules`

### 4.5 Payments Policy (tenant policy)
1) Settings  Payments Policy tabını aç.
2) min/max deposit/withdraw ve payout retry/cooldown ayarlarını değiştir.
3) **Kaydet**.

**API çağrıları:**
- `GET /api/v1/tenants/payments/policy`
- `PUT /api/v1/tenants/payments/policy`

### 4.6 Defaults (read-only)
1) Settings  Defaults tabını aç.
2) Değerleri kontrol et.

**API çağrıları:**
- `GET /api/v1/settings/platform-defaults`

### 4.7 API Keys (settings içi)
1) Settings  API Keys tabını aç.
2) **Generate Key** tıkla.

**API çağrıları:**
- `GET /api/v1/settings/api-keys`
- `POST /api/v1/settings/api-keys/generate`

### 4.8 Versions (UI  backend version)
1) Settings  Versions tabını aç.
2) **Check Backend Version** tıkla.

**API çağrıları:**
- `GET /api/v1/version`

---

## 5) Saha rehberi (pratik ipuçları)

- Settingsi incident çözümü için değil, **konfigürasyon** için kullan.
- Incidentte:
  - kanıt: Logs + Audit Log
  - mitigasyon: Kill Switch
- Değişiklikleri low-traffic saatlerde uygula.
- Şunları not al:
  - ne değişti
  - neden
  - rollback koşulu

---

## 6) Olası hatalar (Belirti  Muhtemel neden  Çözüm  Doğrulama)

1) **Belirti:** Brands tabı yok görünüyor veya loadda hata veriyor.
   - **Muhtemel neden:** backend array yerine object dönüyor (contract mismatch).
   - **Çözüm:** `/api/v1/settings/brands` response shapeini kontrol et; backendi JSON array dönecek şekilde hizala.
   - **Doğrulama:** UI listesi render olur; Network 200 + array payload.

2) **Belirti:** Brand create 404 ile fail.
   - **Muhtemel neden:** `POST /api/v1/settings/brands` implement edilmemiş.
   - **Çözüm:** POST route implement et veya create butonunu gizle.
   - **Doğrulama:** create 200/201 döner ve brand listede görünür.

3) **Belirti:** Currencies tabı hata veriyor.
   - **Muhtemel neden:** `/api/v1/settings/currencies` endpointleri eksik.
   - **Çözüm:** currencies CRUD implement et veya deterministik stub sağla.
   - **Doğrulama:** GET list döner; create/edit listede görünür.

4) **Belirti:** Payments Policy save 403.
   - **Muhtemel neden:** admin tenant policy update yetkisine sahip değil.
   - **Çözüm:** platform owner ile dene veya `require_tenant_policy_admin` davranışını doğrula.
   - **Doğrulama:** PUT 200; GET değişikliği gösterir.

5) **Belirti:** Countries listesi boş.
   - **Muhtemel neden:** kural yok veya endpoint empty.
   - **Çözüm:** default ülke kurallarını seed et; tenant scopeu doğrula.
   - **Doğrulama:** liste dolar.

6) **Belirti:** Placeholder tablar operatörü yanıltıyor.
   - **Muhtemel neden:** UI placeholder tablar açık bırakılmış.
   - **Çözüm:** dokümante et; mümkünse backend gelene kadar tabları gizle.
   - **Doğrulama:** operatör placeholder tablara güvenmeyi bırakır.

7) **Belirti:** Versions tabında backend version çekilemiyor.
   - **Muhtemel neden:** `/api/v1/version` erişilemiyor veya auth blok.
   - **Çözüm:** route var mı kontrol et; erişim politikasını doğrula.
   - **Doğrulama:** toast backend versionı gösterir.

8) **Belirti:** Settings açılıyor ama değişiklikler etkili olmuyor.
   - **Muhtemel neden:** cache veya downstream servis config reload etmiyor.
   - **Çözüm:** propagation kontrol et; gerekiyorsa servis restart.
   - **Doğrulama:** davranış değişir; loglar reloadu gösterir.

9) **Belirti:** Settings değişiklikleri için audit kanıtı yok.
   - **Muhtemel neden:** routelar audited değil.
   - **Çözüm:** settings mutationlarına audit ekle; geçici olarak container log ile kanıtla.
   - **Doğrulama:** Audit Log settings change eventlerini gösterir.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Belirti:** Brands endpointi array yerine `{ items: [...] }` dönüyor.
   - **Muhtemel neden:** backend `GET /api/v1/settings/brands` `{ items: [...] }` dönüyor; UI array bekliyor.
   - **Etki:** Brands listesi Henüz marka yok gibi görünür.
   - **Admin workaround:** Yok (contract sorunu). Tenant lifecycle için Tenants menüsünü kullan.
   - **Escalation paketi:**
     - Method + path: `GET /api/v1/settings/brands`
     - Beklenen vs gerçek: `[]` vs `{ items: [...] }`
     - Anahtar kelime: `settings/brands`
   - **Resolution owner:** Backend
   - **Doğrulama:** GET JSON array döner ve UI listesi render olur.

2) **Belirti:** Settings altındaki birçok endpoint muhtemelen eksik/stub.
   - **Muhtemel neden:** `backend/app/routes/settings.py` şu an minimal stub.
   - **Etki:** Settings UI prod seviyesinde config konsolu olarak kullanılamaz.
   - **Admin workaround:**
     - Mümkünse Tenants, API Keys gibi dedicated menüleri kullan.
     - Payments Policy sadece endpointler varsa kullanılmalı.
   - **Escalation paketi:**
     - DevToolstan 404/500 dönen endpointleri tab bazlı yakala.
   - **Resolution owner:** Backend
   - **Doğrulama:** Her Settings tabının endpointi 200 + doğru schema döner.

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Tab değişince dataset yüklenmeli.
- Create/update sonrası refresh ile değişiklik görünmeli.

### 8.2 System  Logs
- Settings endpointlerinde 4xx/5xx varsa Error Logsa bak.

### 8.3 System  Audit Log
- Settings değişiklikleri burada görünmeli (audit varsa).

### 8.4 DB doğrulama (varsa)
- Brand/currency/country tabloları güncellenir (implementasyona göre).
- Tenant policy tenant confige yazılır.

---

## 9) Güvenlik notları + rollback

- Settings değişiklikleri compliance, payments ve UX üzerinde etkili olabilir.
- Rollback stratejisi:
  - son değişikliği geri al
  - davranış geri döndü mü doğrula
  - kanıt paketi üret (Audit Log + Logs)

---

## 10) İlgili linkler

- Tenants: `/docs/new/tr/admin/system/tenants.md`
- API Keys (System): `/docs/new/tr/admin/system/api-keys.md`
- Payments Policy (yetkiler): `/docs/new/tr/admin/roles-permissions.md`
- Kill Switch: `/docs/new/tr/admin/operations/kill-switch.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
