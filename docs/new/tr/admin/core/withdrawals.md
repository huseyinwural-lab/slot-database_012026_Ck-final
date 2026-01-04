# Withdrawals (TR)

**Menü yolu (UI):** Core → Withdrawals  
**Frontend route:** `/withdrawals`  
**Sadece owner:** Evet (menu config)  

---

## 1) Amaç ve kapsam

Withdrawals menüsü, withdrawal işlemlerini inceleme, approve/reject, payout retry ve “mark paid” aksiyonlarını yönetmek içindir. Operasyonel olarak en çok incident çıkan alanlardan biridir.

---

## 2) Kim kullanır / yetki gereksinimi

- Sadece Platform Owner / Finance Ops (owner-level).

---

## 3) Alt başlıklar / fonksiyon alanları

Mevcut UI (`frontend/src/pages/FinanceWithdrawals.jsx`):
- Filtreler (state, date_from/date_to, amount range, player id)
- Withdrawals tablosu
- Aksiyonlar:
  - Approve
  - Reject (reason)
  - Retry payout
  - Mark paid

---

## 4) Temel akışlar (adım adım)

### 4.1 Withdrawal filtreleme
1) Withdrawals aç.
2) Filtreleri ayarla:
   - state
   - date range
   - min/max amount
   - player_id
3) Apply/refresh.

**API çağrıları (backend destekli):**
- Liste: `GET /api/v1/finance/withdrawals?state=<...>&limit=<n>&offset=<n>&player_id=<...>&date_from=<...>&date_to=<...>&min_amount=<...>&max_amount=<...>&sort=<...>`

### 4.2 Withdrawal approve
1) `requested` state’de withdrawal seç.
2) **Approve** tıkla.
3) Reason gir (önerilir).

**API çağrıları (backend destekli):**
- Review: `POST /api/v1/finance/withdrawals/{tx_id}/review` body `{ action: "approve", reason }`

### 4.3 Withdrawal reject
1) `requested` state’de withdrawal seç.
2) **Reject** tıkla.
3) Reason gir.

**API çağrıları:**
- Review: `POST /api/v1/finance/withdrawals/{tx_id}/review` body `{ action: "reject", reason }`

### 4.4 Payout retry (stuck/failed)
1) Failed/stuck withdrawal tespit et.
2) **Retry** tıkla.
3) Reason gir (backend zorunlu).

**API çağrıları (backend destekli):**
- Retry: `POST /api/v1/finance-actions/withdrawals/{tx_id}/retry` body `{ reason }`

### 4.5 Mark paid
1) Provider tarafında payout tamamlandı mı doğrula.
2) **Mark Paid** tıkla.
3) Reason gir.

**API çağrıları (backend destekli):**
- Mark paid: `POST /api/v1/finance/withdrawals/{tx_id}/mark-paid` body `{ reason }`

---

## 5) Saha rehberi (pratik ipuçları)

- Mutlaka kaydet: tx_id, player_id, amount, currency, state, provider.
- Approve öncesi KYC ve risk kontrolleri tamam olmalı.
- Reject, held fonları available’a geri döndürmelidir (beklenen davranış).

**Yapmayın:**
- Reason yazmadan approve.

---

## 6) Olası hatalar (Semptom → Muhtemel neden → Çözüm → Doğrulama)

1) **Semptom:** Withdrawal listesi yüklenmiyor.
   - **Muhtemel neden:** backend error veya auth invalid.
   - **Çözüm:** owner rolünü doğrula; `/api/v1/finance/withdrawals` Network çağrısına bak.
   - **Doğrulama:** liste endpoint’i items + meta döner.

2) **Semptom:** Approve 400 INVALID_ACTION.
   - **Muhtemel neden:** client unsupported action gönderdi.
   - **Çözüm:** action `approve` veya `reject` olmalı.
   - **Doğrulama:** review çağrısı 200.

3) **Semptom:** Reject sonrası oyuncu refund olmuyor (held düşmüyor).
   - **Muhtemel neden:** ledger delta hata nedeniyle uygulanmadı.
   - **Çözüm:** backend log kontrol; reject tekrar dene; ledger service fail ise escalate.
   - **Doğrulama:** available artar, held azalır.

4) **Semptom:** Retry 400 “Reason is required”.
   - **Muhtemel neden:** UI reason göndermedi.
   - **Çözüm:** reason ekleyip tekrar dene.
   - **Doğrulama:** retry `retry_initiated`.

5) **Semptom:** Retry 422 PAYMENT_RETRY_LIMIT_EXCEEDED.
   - **Muhtemel neden:** tenant policy retry limit dolu.
   - **Çözüm:** tekrar deneme; payments engineering’e escalate; manuel çözümü değerlendir.
   - **Doğrulama:** `FIN_PAYOUT_RETRY_BLOCKED` audit event var.

6) **Semptom:** Retry 429 PAYMENT_COOLDOWN_ACTIVE.
   - **Muhtemel neden:** cooldown süresi dolmadı.
   - **Çözüm:** kalan süreyi bekle; sonra tekrar dene.
   - **Doğrulama:** cooldown sonrası retry başarı.

7) **Semptom:** Mark Paid fail.
   - **Muhtemel neden:** state transition invalid (approved değil) veya reason eksik.
   - **Çözüm:** withdrawal approved mı doğrula; reason ekle.
   - **Doğrulama:** state `paid` olur.

8) **Semptom:** Duplicate withdrawal request.
   - **Muhtemel neden:** player gecikmede retry; idempotency yok.
   - **Çözüm:** duplicate’leri tespit et; birini approve; diğerlerini reject reason ile.
   - **Doğrulama:** tek payout attempt ilerler.

9) **Semptom:** Provider error / payout başarısız.
   - **Muhtemel neden:** provider outage, bank detayları invalid, provider reject.
   - **Çözüm:** provider status kontrol; metadata doğrula; policy’ye göre retry.
   - **Doğrulama:** payout attempt status submitted/paid’e geçer.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Semptom:** UI “Retry” başarılı görünüyor ama payout status değişmiyor.
   - **Muhtemel neden:** provider entegrasyonu mock/stub veya async worker çalışmıyor.
   - **Impact:** Withdrawal stuck kalır; operasyon bloklanır.
   - **Admin Workaround:** Dış sistemden ödeme tamam kanıtı olmadan “mark paid” yapma; kanıt varsa “mark paid” kullan, yoksa durdurup escalate.
   - **Escalation Package:**
     - Method + path: `POST /api/v1/finance-actions/withdrawals/{tx_id}/retry`
     - Request sample: `{ "reason": "<text>" }`
     - Expected vs actual: expected `retry_initiated` + state progression; actual no progression
     - Log: `FIN_PAYOUT_RETRY_INITIATED`, `Adyen Payout Failed`, `provider error`, `attempt_id`
   - **Resolution Owner:** Backend / Payments
   - **Verification:** Retry sonrası payout attempt transition ve withdrawal state update.

---

## 8) Doğrulama (UI + Log + Audit + DB)

### 8.1 UI
- Tablo üzerinde state geçişleri görünür.

### 8.2 System → Logs
- finance-actions üzerinde 4xx/5xx artışı var mı kontrol et.

### 8.3 Container/app log
- Arama anahtar kelimeleri:
  - `FIN_WITHDRAW_APPROVED` / `FIN_WITHDRAW_REJECTED`
  - `FIN_PAYOUT_RETRY_INITIATED` / `FIN_PAYOUT_RETRY_BLOCKED`
  - `Adyen Payout Failed`

### 8.4 System → Audit Log
- Beklenen action’lar:
  - `FIN_WITHDRAW_APPROVED`
  - `FIN_WITHDRAW_REJECTED`
  - `FIN_PAYOUT_RETRY_INITIATED`

### 8.5 DB audit (varsa)
- `transaction`: `state`, `status`, `reviewed_by`, `reviewed_at`, `review_reason`.
- `payoutattempt`: `withdraw_tx_id` bazlı attempt’ler.
- `auditevent`: evidence.

---

## 9) Güvenlik notları + geri dönüş

- Withdrawals yüksek risklidir. Kanıt olmadan approve edilmez.
- Geri dönüş:
  - Yanlış approve ve henüz paid değilse: policy izin veriyorsa reject + held refund.
  - Paid olduysa: incident + dispute/chargeback süreci.

---

## 10) İlgili linkler

- KYC: `/docs/new/tr/admin/operations/kyc-verification.md`
- Risk Rules: `/docs/new/tr/admin/risk-compliance/risk-rules.md`
- Sık hatalar: `/docs/new/tr/guides/common-errors.md`
