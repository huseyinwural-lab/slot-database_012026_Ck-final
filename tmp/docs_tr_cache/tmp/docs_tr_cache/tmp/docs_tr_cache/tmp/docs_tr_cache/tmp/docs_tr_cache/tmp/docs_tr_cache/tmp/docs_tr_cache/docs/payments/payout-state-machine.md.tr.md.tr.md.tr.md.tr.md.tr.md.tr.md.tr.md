# Payout State Machine (P0-5)

## Amaç

Withdraw "paid" adımını PSP payout succeed olmadan asla ledger'a yazmamak; payout fail/partial/retry
senaryolarında double-debit'i sıfırlamak ve held bakiyenin her zaman deterministik olmasını sağlamak.

## State'ler (Önerilen Model)

Withdrawal için önerilen state diyagramı:

- `requested`
  - Kullanıcı withdraw talebini oluşturduğunda.
  - Invariants:
    - `available -= amount`
    - `held += amount`

- `approved`
  - Risk/finance ekibi tarafından onaylandığında.
  - Sadece state değişir, balance değişmez.

- `payout_pending`
  - Payout işlemi provider'a gönderildi, sonuç bekleniyor.
  - Balance değişmez; held hâlâ kilitli.

- `paid`
  - Provider payout succeed döndüğünde.
  - Invariants:
    - `held -= amount` (outflow)
    - `withdraw_paid` ledger event **yalnızca bu noktada** yazılır.

- `payout_failed`
  - Provider payout fail döndüğünde.
  - Invariants:
    - `held` değişmez (hala kilitli fon)
    - `withdraw_paid` ledger event **yazılmaz**.
  - Bu state retryable; admin "retry payout" veya "reject" kararına göre ilerler.

- `rejected`
  - Admin withdraw talebini reddettiğinde.
  - Invariants:
    - `available += amount`
    - `held -= amount` (rollback)

## Geçiş Kuralları

- `requested -> approved`
  - Koşul: Admin approve.
  - Balance: değişmez.

- `requested -> rejected`
  - Koşul: Admin reject.
  - Balance:
    - `available += amount`
    - `held -= amount`

- `approved -> payout_pending`
  - Koşul: Admin "start payout" / "mark-paid" aksiyonuna bastı.
  - Balance: değişmez.
  - Side-effect: PSP'ye payout isteği gönderilir; yeni `PayoutAttempt` kaydı açılır.

- `payout_pending -> paid`
  - Koşul: Provider payout succeed (ya senkron response ya webhook).
  - Balance:
    - `held -= amount`
  - Ledger:
    - `withdraw_paid` ledger event **yalnızca bu geçişte** oluşturulur.

- `payout_pending -> payout_failed`
  - Koşul: Provider payout fail.
  - Balance:
    - `held` korunur.
  - Ledger:
    - `withdraw_paid` event'i yazılmaz.

- `payout_failed -> payout_pending`
  - Koşul: Admin "retry payout".
  - Balance: değişmez.
  - Yeni PayoutAttempt açılır veya mevcut attempt idempotent şekilde reuse edilir.

- `payout_failed -> rejected`
  - Koşul: Admin withdraw'u iptal etmeye karar verir.
  - Balance:
    - `available += amount`
    - `held -= amount`

## Payout ile İlgili Ledger Kuralları

- `withdraw_requested` event'i hold move'u temsil eder:
  - `delta_available = -amount`
  - `delta_held = +amount`

- `withdraw_rejected` event'i rollback'i temsil eder:
  - `delta_available = +amount`
  - `delta_held = -amount`

- `withdraw_paid` event'i **sadece payout succeed** olduğunda yazılır:
  - `delta_available = 0`
  - `delta_held = -amount`

- Payout fail durumlarında (`payout_failed` state):
  - `withdraw_paid` event'i **yoktur**.
  - Held fonlar kilitli kalır; admin daha sonra reject veya retry kararına göre ilerler.

## API Kontrat Taslağı

### Start Payout (idempotent)

- Endpoint (öneri):
  - `POST /api/v1/finance/withdrawals/{id}/payout`

- Girdi:
  - Header: `Idempotency-Key: <uuid>`

- Davranış:
  - Eğer withdraw state `approved` değilse:
    - `409 INVALID_STATE_TRANSITION`.
  - Aynı key + aynı payload için tekrar çağrı:
    - `200 OK` + mevcut `PayoutAttempt` kaydı (no-op).
  - Aynı key + farklı payload:
    - `409 IDEMPOTENCY_KEY_REUSE_CONFLICT`.

### Payout Webhook / Provider Callback

- Provider'dan gelen success/fail event'leri için:
  - `provider_event_id` ile dedupe.
  - Success → `payout_pending -> paid` + `withdraw_paid` ledger event.
  - Fail → `payout_pending -> payout_failed` (ledger'da paid yok).
  - Replay (aynı provider_event_id) → 200 OK + no-op.

## UI Beklentileri (Admin Panel)

- State Badge'leri:
  - `requested`, `approved`, `payout_pending`, `payout_failed`, `paid`, `rejected`.

- Aksiyon Butonları:
  - `requested`: Approve, Reject.
  - `approved`: Start payout (veya Mark-paid, yeni anlamıyla).
  - `payout_pending`: Recheck.
  - `payout_failed`: Retry payout, Reject.
  - `paid` / `rejected`: aksiyon yok.

Bu doküman, backend state machine implementasyonu ve admin UI tasarımı için tek kaynak sözleşme olarak kullanılmalıdır.
