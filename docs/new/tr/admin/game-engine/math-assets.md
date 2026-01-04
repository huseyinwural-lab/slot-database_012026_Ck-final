# Math Assets (TR)

**Menü yolu (UI):** Game Engine → Math Assets  
**Frontend route:** `/math-assets`  
**Feature flag (UI):** `can_use_game_robot`  

---

## Ops Checklist (read first)

- Math Assets, Robots tarafından kullanılan ağır math verisidir (paytable, reelset).
- Upload/replace prod etkili işlemdir:
  - **reason** zorunlu (backend enforce eder)
  - **Audit Log**’da izlenebilir olmalı
- Yeni asset’i referanslayan robot enable edilmeden önce:
  - asset var mı doğrula
  - JSON geçerli mi doğrula

---

## 1) Amaç ve kapsam

Math Assets, robot’ların referansladığı math verisini saklar:
- `paytable`
- `reelset`

Frontend: `frontend/src/pages/MathAssetsPage.jsx`.
Backend: `backend/app/routes/math_assets.py`.

---

## 2) Kim kullanır / yetki gereksinimi

- Game Engine / Math Ops

Erişim:
- UI: `can_use_game_robot`
- Backend: admin auth

---

## 3) UI’da neler var?

- ref_key ile arama
- type filter (paytable/reelset)
- JSON content görüntüleme
- Yeni asset upload (JSON)

> Not: UI upload (POST) var; replace akışı yok.

---

## 4) Temel akışlar

### 4.1 Asset listeleme/arama
1) Game Engine → Math Assets aç.
2) ref_key ile ara.
3) type filter uygula.

**API çağrıları (UI):**
- `GET /api/v1/math-assets?search=<text>&type=<paytable|reelset|all>`

Beklenen response:
- `{ items: MathAsset[], meta: { total, page, page_size } }`

### 4.2 Asset content görüntüleme
1) Eye tıkla.
2) JSON incele.

### 4.3 Yeni asset upload
1) **Upload New Asset**.
2) Doldur:
   - ref_key (unique)
   - type (paytable/reelset)
   - JSON content
3) Upload.

**API çağrıları:**
- `POST /api/v1/math-assets`

**Body (UI):**
- `{ ref_key, type, content }`

**Backend gereksinimi:**
- audit reason `X-Reason` header veya `reason` field.

**Audit event (beklenen):**
- `MATH_ASSET_UPLOAD`

### 4.4 Var olan asset’i replace (backend capability)
Backend replace destekler.

**API çağrıları:**
- `POST /api/v1/math-assets/{asset_id}/replace`

**Reason:**
- replace için `X-Reason` header zorunlu.

---

## 5) Saha rehberi (pratik ipuçları)

- Versiyonlu ref key kullan: `basic_pay_v1`, `basic_pay_v2`.
- In-place replace yerine yeni ref key tercih et (rollback daha temiz).
- JSON schema’yı upload öncesi offline doğrula.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Asset listesi boş.
   - **Muhtemel neden:** asset yok veya tenant mismatch.
   - **Çözüm:** seed; tenant context doğrula.
   - **Doğrulama:** GET items döner.

2) **Belirti:** Upload “Invalid JSON content”.
   - **Muhtemel neden:** JSON geçersiz.
   - **Çözüm:** JSON validate.
   - **Doğrulama:** upload ilerler.

3) **Belirti:** Upload 400 REASON_REQUIRED.
   - **Muhtemel neden:** backend reason ister, UI göndermiyor.
   - **Çözüm:** UI’a reason alanı ekle veya `X-Reason` header.
   - **Doğrulama:** POST 200.

4) **Belirti:** Upload 409 conflict.
   - **Muhtemel neden:** ref_key zaten var.
   - **Çözüm:** yeni ref_key veya replace.
   - **Doğrulama:** upload success.

5) **Belirti:** Upload 400 “Missing required fields”.
   - **Muhtemel neden:** ref_key/type/content eksik.
   - **Çözüm:** alanları doldur.
   - **Doğrulama:** POST kabul.

6) **Belirti:** Replace 400 REASON_REQUIRED.
   - **Muhtemel neden:** `X-Reason` header yok.
   - **Çözüm:** header ekle.
   - **Doğrulama:** replace success.

7) **Belirti:** Robot asset ref_key var ama simülasyon fail.
   - **Muhtemel neden:** asset schema hatalı.
   - **Çözüm:** schema doğrula; düzeltilmiş versiyon upload.
   - **Doğrulama:** simülasyon çalışır.

8) **Belirti:** Audit Log’da asset değişiklikleri yok.
   - **Muhtemel neden:** audit görünür değil veya persist yok.
   - **Çözüm:** Audit Log route/filter; audit.log_event çağrısı.
   - **Doğrulama:** `MATH_ASSET_UPLOAD`/`MATH_ASSET_REPLACE` görünür.

9) **Belirti:** Upload başarılı ama list refresh olmuyor.
   - **Muhtemel neden:** client state güncellenmedi.
   - **Çözüm:** refresh; GET doğrula.
   - **Doğrulama:** asset görünür.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI audit reason göndermez; backend reason zorunlu.
   - **Muhtemel neden:** backend `X-Reason`/`reason` okur ve REASON_REQUIRED fırlatır.
   - **Etki:** upload/replace fail olabilir.
   - **Admin workaround:** yok.
   - **Escalation paketi:** 400 response.
   - **Resolution owner:** Frontend/Backend

2) **Belirti:** UI’da replace yok, backend var.
   - **Muhtemel neden:** UI’da Replace butonu yok.
   - **Etki:** hotfix zor; yeni ref_key ile ilerlenir.
   - **Resolution owner:** Frontend/Product

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Upload success toast.
- Asset listede görünür.

### 8.2 System → Logs
- `/api/v1/math-assets` 4xx/5xx kontrol.

### 8.3 System → Audit Log
- `MATH_ASSET_UPLOAD`, `MATH_ASSET_REPLACE` filtre.

### 8.4 DB doğrulama
- `mathasset` satırları.

---

## 9) Güvenlik notları + rollback

- Math assets payout davranışını dolaylı etkiler.
- Rollback:
  - robot binding’i eski asset ref_key’ye çevir
  - veya asset content’i önceki versiyonla replace (sıkı change control gerekir)

---

## 10) İlgili linkler

- Robots: `/docs/new/tr/admin/game-engine/robots.md`
- Simulator: `/docs/new/tr/admin/system/simulator.md`
- Audit Log: `/docs/new/tr/admin/system/audit-log.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
