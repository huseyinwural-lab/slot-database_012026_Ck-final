# Affiliates (TR)

**Menü yolu (UI):** Operations → Affiliates  
**Frontend route:** `/affiliates`  
**Feature flag (UI):** `can_manage_affiliates`  

---

## Ops Checklist (read first)

- Modül enabled mı kontrol et (Kill Switch: `affiliates`).
- Partner/offer/link/payout için:
  - request/response kanıtı topla
  - onay kararını (neden) kayıt altına al
- Abuse riskini izle (self-referral, bonus abuse).

---

## 1) Amaç ve kapsam

Affiliates, acquisition partner yönetimidir:
- partners (affiliates)
- offers
- tracking links
- payouts
- creatives

Frontend: `frontend/src/pages/AffiliateManagement.jsx`.
Backend: `backend/app/routes/affiliates.py`.

---

## 2) Kim kullanır / yetki gereksinimi

- Growth/Marketing Ops
- Finance (payout)

Erişim:
- UI: `can_manage_affiliates`
- Backend: `enforce_module_access(..., module_key="affiliates")`

---

## 3) Alt başlıklar / tab’lar (UI)

AffiliateManagement tab’ları:
- Partners
- Offers
- Tracking
- Payouts
- Creatives
- Reports

---

## 4) Temel akışlar

### 4.1 Partners list + create
**API çağrıları (UI):**
- `GET /api/v1/affiliates`
- `POST /api/v1/affiliates`

### 4.2 Offers
**API çağrıları (UI):**
- `GET /api/v1/affiliates/offers`
- `POST /api/v1/affiliates/offers`

### 4.3 Tracking links
**API çağrıları (UI):**
- `GET /api/v1/affiliates/links`
- `POST /api/v1/affiliates/links`

### 4.4 Payouts
**API çağrıları (UI):**
- `GET /api/v1/affiliates/payouts`
- `POST /api/v1/affiliates/payouts`

### 4.5 Creatives
**API çağrıları (UI):**
- `GET /api/v1/affiliates/creatives`
- `POST /api/v1/affiliates/creatives`

---

## 5) Operasyon notları

- Partner onayı şunları içermeli:
  - business doğrulama
  - traffic source incelemesi
  - payout terms
- Kanal bazlı ayrı tracking link kullan.

---

## 6) Olası hatalar (Belirti → Muhtemel neden → Çözüm → Doğrulama)

1) **Belirti:** Affiliates menüsü görünmüyor.
   - **Muhtemel neden:** `can_manage_affiliates` yok.
   - **Çözüm:** feature ver.
   - **Doğrulama:** menü görünür.

2) **Belirti:** Affiliates endpoint’leri 503.
   - **Muhtemel neden:** Kill Switch modülü kapattı.
   - **Çözüm:** `affiliates` enable.
   - **Doğrulama:** endpoint 200.

3) **Belirti:** Offers/Payouts/Creatives tab’ları hep boş.
   - **Muhtemel neden:** backend stub `[]`.
   - **Çözüm:** persistence implement.
   - **Doğrulama:** created item görünür.

4) **Belirti:** Partner create 422.
   - **Muhtemel neden:** zorunlu alan eksik.
   - **Çözüm:** form validation.
   - **Doğrulama:** partner oluşur.

5) **Belirti:** Offer create 404.
   - **Muhtemel neden:** backend route yok.
   - **Çözüm:** `/affiliates/offers` implement.
   - **Doğrulama:** offer oluşur.

6) **Belirti:** Tracking link üretilemiyor.
   - **Muhtemel neden:** backend farklı schema bekliyor.
   - **Çözüm:** `newLink` contract hizala.
   - **Doğrulama:** link listede ve URL copy edilebilir.

7) **Belirti:** Payout var ama finance reconcile edemiyor.
   - **Muhtemel neden:** period metadata/ledger ref yok.
   - **Çözüm:** period_start/period_end + ledger ref.
   - **Doğrulama:** payout trace edilebilir.

8) **Belirti:** Affiliate değişiklikleri için audit yok.
   - **Muhtemel neden:** route’lar audited değil.
   - **Çözüm:** audit event ekle.
   - **Doğrulama:** Audit Log entry’leri var.

9) **Belirti:** Self-referral abuse.
   - **Muhtemel neden:** anti-fraud check yok.
   - **Çözüm:** Risk Rules entegrasyonu; affiliate KYC.
   - **Doğrulama:** şüpheli trafik bloklanır.

---

## 7) Backend/Integration Gap’leri (Release Note)

1) **Belirti:** UI’ın çağırdığı endpoint’lerin bir kısmı implement değil.
   - **Muhtemel neden:** `backend/app/routes/affiliates.py` base CRUD + stub içeriyor.
   - **Etki:** Offers/Payouts/Creatives prod seviyesinde çalışmaz.
   - **Admin workaround:** harici takip.
   - **Escalation paketi:** data model + endpoint.
   - **Resolution owner:** Backend

---

## 8) Doğrulama (UI + Logs + Audit + DB)

### 8.1 UI
- Partner create olur ve listede görünür.

### 8.2 System → Logs
- `/api/v1/affiliates*` hataları kontrol.

### 8.3 System → Audit Log
- affiliate create/approve/payout event’leri (varsa).

### 8.4 DB doğrulama
- tenant bazlı `affiliate` satırları.

---

## 9) Güvenlik notları

- Traffic source doğrulaması yap.
- GDPR/consent gereksinimleri.

---

## 10) İlgili linkler

- Kill Switch: `/docs/new/tr/admin/operations/kill-switch.md`
- Risk Rules: `/docs/new/tr/admin/risk-compliance/risk-rules.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
