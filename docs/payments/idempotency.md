# Payments Idempotency Contract

This document defines the canonical idempotency contract for all money-path actions (deposit/withdraw/payout/recheck) and payout webhooks.

## 0) Terminology

- **Money-path action**: an API call that can move real balances or create/transition a financial transaction.
- **Idempotency**: repeating the same request should not create duplicate effects (double charge, double ledger, double state transition).
- **Dedupe key**: a stable identifier used to detect replays (client idempotency key, provider event id, ledger event idempotency key).

---

## 1) Idempotency Header (Client → API)

### 1.1 Canonical header name

- **`Idempotency-Key`** is the only standard header used across FE/BE.

No alternatives are supported (e.g., `X-Idempotency-Key`).

### 1.2 Required vs legacy endpoints

**Target contract (P0):**
- All money-path *create/action* endpoints MUST require `Idempotency-Key`.
- Missing key MUST return `400 IDEMPOTENCY_KEY_REQUIRED`.

**Current reality:**
- New critical endpoints (payout / recheck and all new money actions) enforce the requirement.
- Some legacy endpoints may still accept missing keys (best-effort idempotency). These will be hardened to the target contract incrementally.

> Rule of thumb: If an endpoint can cause balance/ledger changes, the target state is **Idempotency-Key required**.

---

## 2) Canonical Key Formats (FE → BE)

### 2.1 Admin actions

Format:

```text
admin:{txId}:{action}:{nonce}
```

- `txId`: withdrawal transaction id
- `action` (canonical set):
  - `approve`
  - `reject`
  - `mark_paid` (legacy manual settlement)
  - `payout_start`
  - `payout_retry`
  - `recheck`
- `nonce`: generated once per `(txId, action)` attempt and persisted until the request resolves (success/failure).

### 2.2 Player actions

Format:

```text
player:{playerId}:{action}:{nonce}
```

- `action` (canonical set):
  - `deposit`
  - `withdraw`

---

## 3) UI Behavior (Double-click, Retry)

### 3.1 In-flight locking

For the same `(scope, id, action)`:

- Disable the action button while request is in-flight.
- Ensure multiple clicks reuse the same nonce → same `Idempotency-Key`.
- On completion (success/failure), release the lock.

### 3.2 Retry policy

A retry MUST reuse the exact same `Idempotency-Key`.

**Retryable:**
- network errors / timeouts
- 502, 503, 504

**Non-retryable:**
- all 4xx (especially 401, 403, 409, 422)
- other 5xx (unless explicitly decided otherwise)

**Recommended defaults:**
- max retries: 2
- backoff: small deterministic delays (avoid long exponential waits in UI flows)

---

## 4) Server Semantics (201/200 no-op, 409 conflict)

### 4.1 Successful first create/action

- First-time create/action typically returns **201 Created** (or 200 OK for action endpoints).
- The server performs the single canonical effect:
  - create transaction / transition state
  - write ledger event(s)
  - update balances

### 4.2 Replay (same Idempotency-Key + same payload)

- MUST return 200 OK with the already-created resource/result.
- MUST be a no-op (no new transaction row, no duplicate ledger, no extra state transition).

### 4.3 Conflict (same Idempotency-Key + different payload)

- MUST return **409 Conflict** with:

```json
{
  "error_code": "IDEMPOTENCY_KEY_REUSE_CONFLICT"
}
```

- No side effects allowed.

### 4.4 Invalid state machine transitions

- MUST return **409 Conflict** with:

```json
{
  "error_code": "INVALID_STATE_TRANSITION",
  "from_state": "...",
  "to_state": "...",
  "tx_type": "deposit|withdrawal"
}
```

- No side effects allowed.

---

## 5) Provider Replay Dedupe (Webhook/Event Level)

### 5.1 Canonical dedupe key

Provider webhooks MUST be deduped by:

```text
(provider, provider_event_id)
```

- First webhook with a given `(provider, provider_event_id)` produces the canonical effect.
- Any replay must return 200 OK and be a no-op.

---

## 6) Webhook Signature Security (WEBHOOK-SEC-001)

This section defines the security gate that MUST run before webhook dedupe.

### 6.1 Required headers

```http
X-Webhook-Timestamp: <unix-seconds>
X-Webhook-Signature: <hex>
```

### 6.2 Signed payload

```text
signed_payload = f"{timestamp}.{raw_body}"
signature      = HMAC_SHA256(WEBHOOK_SECRET, signed_payload).hexdigest()
```

- `raw_body` is the raw request body (bytes), not a parsed JSON re-serialization.
- `WEBHOOK_SECRET` is configured via environment/secret store.

### 6.3 Error semantics

- Missing timestamp/signature → `400 WEBHOOK_SIGNATURE_MISSING`
- Timestamp invalid or outside tolerance window (±5 minutes) → `401 WEBHOOK_TIMESTAMP_INVALID`
- Signature mismatch → `401 WEBHOOK_SIGNATURE_INVALID`

### 6.4 Ordering: signature gate → dedupe

Webhook processing order is:

1. Verify signature (reject early if invalid)
2. Replay dedupe by `(provider, provider_event_id)`
3. Apply canonical state/ledger effects (exactly once)

---

## 7) Ledger-Level Idempotency (Real Money Safety)

Certain ledger events MUST be written at most once per logical outcome.

**Example: `withdraw_paid`**

- When a withdrawal reaches the `paid` state via payout success, a `withdraw_paid` ledger event MUST be written exactly once.
- Replays (client retries, webhook replays) MUST not produce additional `withdraw_paid` events.
- Protection is enforced via a combination of:
  - client `Idempotency-Key`
  - provider `(provider, provider_event_id)` dedupe
  - ledger event idempotency keys

---

## 8) Proof Commands (Sprint 1 P0)

**Webhook security tests:**

```bash
cd /app/backend
pytest -q tests/test_webhook_security.py
```

**Tenant policy limits:**

```bash
cd /app/backend
pytest -q tests/test_tenant_policy_limits.py
alembic heads
alembic upgrade head
```

**Money path E2E (previously stabilized):**

```bash
cd /app/e2e
yarn test:e2e tests/money-path.spec.ts
```

---

## 9) One-line closure

WEBHOOK-SEC-001, TENANT-POLICY-001, IDEM-DOC-001 and TX-STATE-001 together define and prove (code + tests + docs) the money-path idempotency, webhook security, daily limit gating, and transaction state machine contracts as a single source of truth.
