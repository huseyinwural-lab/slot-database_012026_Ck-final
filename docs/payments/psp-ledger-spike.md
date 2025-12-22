# PSP + Ledger Evrimi — Design Spike (Karar Seti)

## 0) Temel İlke

**Ledger canonical (source of truth) olmalı.** PSP, dış dünyadan gelen ödeme olaylarını sağlayan bir provider; ledger ise bakiye, muhasebe ve raporlamanın tek doğrusu.

Böylece:
- Provider arızasında bile sistem iç tutarlılık korunur.
- "İki kez webhook geldi" veya "client tekrar denedi" gibi gerçek dünyada kaçınılmaz durumlar deterministik yönetilir.
- Reconciliation (sağlama) ve dispute/chargeback süreçleri ledger üstünden yürür.

---

## 1) Canonical Model: Ledger vs PSP Event Source

**Karar:**
- Ledger canonical: Her para hareketi ledger’da "journal/event" olarak kayıt altına alınır.
- PSP tarafı canonical değildir; PSP sadece:
  - `provider_payment_id` / `provider_payout_id`
  - `event_id` / webhook id
  - provider status (authorized / captured / failed vs.)
  üretir.

### Minimal Veri Modeli (Öneri)

**`ledger_transactions` (immutable event log)**
- `tx_id` (internal UUID / ULID)
- `type`: `deposit | withdraw | adjustment | reversal | fee`
- `direction`: `credit | debit`
- `amount`, `currency`
- `player_id`, `tenant_id`
- `status`: state machine’deki durum
- `idempotency_key` (nullable ama çoğunlukla dolu)
- `provider`: `stripe | adyen | mock | ...` (nullable)
- `provider_ref` (provider payment/payout id)
- `provider_event_id` (webhook event id)
- `created_at`

**`wallet_balances` (materialized view / snapshot)**
- `balance_real_available`
- `balance_real_pending`
- Opsiyonel: `balance_bonus_*`

**`withdrawals` (iş akışı tablosu, UI için)**
- `tx_id` (ledger’a referans)
- `state`, `reviewed_by`, `reviewed_at`, `paid_at`, `balance_after` (snapshot)

> Not: Şu anki sistemde withdrawals + `balance_after` zaten var; ledger evrimi bu yapıyı "harden" eder ve PSP event’leriyle bağlar.

---

## 2) Idempotency Stratejisi (Üç Katman)

### 2.1. Client → Backend (request idempotency)

**Amaç:** Aynı user aksiyonu (deposit/withdraw request) tekrar gönderilse bile tek tx yaratmak.

- Header: `Idempotency-Key`
- Scope: `tenant_id + player_id + endpoint + idempotency_key`
- TTL: 24–72 saat (iş ihtiyacına göre)
- Davranış:
  - İlk istek tx yaratır.
  - Tekrar istek aynı response’u döndürür (200/201 + aynı `tx_id`).

### 2.2. Backend → PSP (provider idempotency)

**Amaç:** Backend retry yaptığında PSP’de çift payment/payout oluşmasın.

- Provider’ın idempotency mekanizması varsa kullanılır (çoğunda var).
- Backend mapping:
  - `internal tx_id` → provider idempotency key
  - Öneri: `psp_idem_key = "tx_" + tx_id` (tek kaynak)

### 2.3. Webhook → Ledger (event idempotency)

**Amaç:** Aynı webhook (veya provider replay) ledger’da çift işlem yaratmasın.

- Unique constraint:
  - `(provider, provider_event_id)` unique
  - Ek safety: `(provider, provider_ref, event_type)` unique (provider_event_id yoksa)
- İşleme kuralı:
  - Event daha önce işlendi ise **no-op + 200 OK**

---

## 3) State Machine Tasarımı

### 3.1. Deposit State Machine

Önerilen minimal akış:

1. `deposit_initiated`
2. `deposit_authorized` (opsiyonel; PSP flow’a bağlı)
3. `deposit_captured` (funds settled/confirmed) → **terminal success**
4. `deposit_failed` → **terminal fail**
5. `deposit_reversed` / `deposit_refunded` → **terminal + compensating**

**Ledger etkisi:**
- initiated/authorized: pending bakiyeye yazılabilir (opsiyonel)
- captured: available artar (credit)
- failed: no credit
- refunded/reversed: available azaltılır (debit reversal)

### 3.2. Withdraw State Machine

Mevcut admin flow ile uyumlu şekilde:

1. `withdraw_requested` (player request)
2. `withdraw_approved` (admin review)
3. `withdraw_paid` (admin/PSP payout completed) → **terminal success**
4. `withdraw_rejected` → **terminal fail**
5. `withdraw_failed` (PSP payout fail) → **terminal fail**
6. `withdraw_reversed` (chargeback/correction) → **terminal compensating**

**Ledger etkisi (kritik karar):**

- `withdraw_requested`: funds hold (available → pending) mi, yoksa doğrudan debit mi?
- **Öneri: hold modeli**
  - requested: `available`’dan düş, `pending`’e al
  - rejected/failed: `pending → available` geri
  - paid: `pending` → çıkış (final debit)

Bu, gerçek ödeme dünyasında en sağlıklı muhasebe modelidir.

---

## 4) Reconciliation Stratejisi (Provider ↔ Ledger)

### Ana Anahtarlar

- `tx_id` (internal)
- `provider_ref` (payment_id / payout_id)
- `provider_event_id` (webhook event id)

### Reconciliation Job (Periyodik)

- Günlük veya saatlik çalışabilir:
  - PSP’den "son 24 saat payment/payout listesi"
  - Ledger’daki `provider_ref` ile eşleştir
  - Uyuşmayanları "attention queue"ya düşür:
    - PSP captured ama ledger captured değil
    - Ledger captured ama PSP failed

- Çıktı:
  - `reconciliation_findings` tablosu
  - Admin ekranı (P2 olabilir)

### Webhook Doğrulama

- Signature verification (PSP’ye bağlı)
- Timestamp tolerance + replay guard
- Yanlış signature → 400/401 (asla process etme)

---

## Spike Deliverables

### Deliverable A — Karar Dokümanı

Bu dosya (`/docs/payments/psp-ledger-spike.md`) repo’ya eklenmiş durumda ve PSP + ledger evrimi için tek sayfalık karar setini içeriyor.

### Deliverable B — EPIC’e Dönüşecek İş Kırılımı (Öneri)

1. **LEDGER-01:** Ledger event log + balances snapshot (migration + repository)
2. **LEDGER-02:** Deposit/Withdraw state machine implementation (domain layer)
3. **PSP-01:** Provider adapter arayüzü + `MockPSP` (test/dev)
4. **PSP-02:** Webhook receiver + signature + idempotent event processing
5. **OPS-01:** Reconciliation job + findings table (P2)

---

## Net Öneri

- **Ledger canonical** + **hold-based withdrawal accounting** ile ilerleyin.
- Idempotency’yi üç katmanda (client, provider, webhook) `unique constraint + cache` kombinasyonuyla kilitleyin.
- Gerçek PSP entegrasyonuna geçmeden önce **MockPSP**’yi canonical hale getirin;
  böylece staging/test ortamında gerçek PSP olmadan state machine’i uçtan uca test edebilirsiniz.