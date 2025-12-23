# Payments Transaction State Machine

This document defines the canonical transaction states and allowed transitions for deposit and withdrawal flows. It also documents the real-balance semantics (available/held) and how tenant daily limits count usage.

---

## 0) Canonical vs UI Labels

The backend stores canonical states. The UI may display simplified labels.

Example:
- Deposit canonical: `created -> pending_provider -> completed|failed`
- UI label: often shown as a single `pending` phase (covers both `created` and `pending_provider`)

---

## 1) Canonical State Set

### 1.1 Deposit states (core)

- `created`
- `pending_provider`
- `completed`
- `failed`

### 1.2 Withdrawal states (core)

- `requested`
- `approved`
- `rejected`
- `canceled`

### 1.3 Payout reliability extension (P0-5)

- `payout_pending`
- `payout_failed`
- `paid`

---

## 2) Deposit State Machine

### 2.1 Diagram

```text
created -> pending_provider -> completed | failed
```

### 2.2 Allowed transitions (canonical)

- `created → pending_provider`
- `pending_provider → completed | failed`

### 2.3 UI representation

UI may group early states:

- `created + pending_provider ⇒ pending` (display-only alias)

---

## 3) Withdrawal State Machine

### 3.1 Modern PSP payout path

```text
requested      -> approved | rejected | canceled
approved       -> payout_pending
payout_pending -> paid | payout_failed
payout_failed  -> payout_pending | rejected
```

### 3.2 Legacy manual settlement path

```text
approved -> paid
```

- This path is intentionally preserved for Admin **"Mark Paid"** (PSP bypass / manual settlement).
- Modern PSP payout path remains preferred for provider-integrated payouts.

### 3.3 Allowed transitions (canonical)

- `requested → approved | rejected | canceled`
- `approved → paid | payout_pending`
- `payout_pending → paid | payout_failed`
- `payout_failed → payout_pending | rejected`

---

## 4) Invalid Transition Error Contract

If a transition is not whitelisted:

```json
HTTP 409
{
  "detail": {
    "error_code": "ILLEGAL_TRANSACTION_STATE_TRANSITION",
    "from_state": "approved",
    "to_state": "requested",
    "tx_type": "withdrawal"
  }
}
```

Notes:

- Transitioning to the same state (e.g., `approved -> approved`) is treated as idempotent no-op.

---

## 5) Real Balance Semantics (Ledger / Wallet)

The system maintains real-money balances with the following canonical fields:

- `balance_real_available`
- `balance_real_held`
- `balance_real_total = balance_real_available + balance_real_held`

### 5.1 Withdrawal holds and settlement semantics

Let `amount` be the withdrawal amount.

#### 5.1.1 On withdrawal request (`requested`)

- `balance_real_available -= amount`
- `balance_real_held += amount`

Purpose: funds are reserved while awaiting approval and payout.

#### 5.1.2 On rejection (`rejected`) or cancel (`canceled`)

- `balance_real_available += amount`
- `balance_real_held -= amount`

Purpose: release reserved funds back to available balance.

#### 5.1.3 On paid settlement (`paid`)

- `balance_real_held -= amount`
- `balance_real_available` remains unchanged

Purpose: reserved funds leave the system (payout completed). The canonical ledger event is `withdraw_paid`, written exactly once.

### 5.2 Deposit semantics

Deposits increase available balance only upon final completion:

- On `completed`:
  - `balance_real_available += amount`

Intermediate provider pending states do not change the balance unless explicitly designed (current contract: no intermediate balance movement).

---

## 6) Tenant Daily Limit Counting (TENANT-POLICY-001)

Tenant daily policy enforcement counts usage by canonical states.

### 6.1 Deposit daily usage

Count deposits where:

- `type = "deposit"`
- `state = "completed"`

### 6.2 Withdraw daily usage

Count withdrawals where:

- `type = "withdrawal"`
- `state IN ("requested", "approved", "paid")`

Notes:

- `failed`, `rejected`, `canceled` do not count toward daily usage.
- This selection is aligned with the canonical state set above and is enforced by TENANT-POLICY-001.

Implementation note: TENANT-POLICY-001 enforcement is expected to follow this exact table; any change here must update both enforcement and tests.

---

## 7) FE/BE Alignment Requirements

When adding a new state:

1. Update backend `ALLOWED_TRANSITIONS` (transaction state machine),
2. Update this document,
3. Update FE badge mapping and action guards (Admin/Tenant/Player surfaces),
4. Add or update tests (unit + E2E where applicable).

---

## 8) Proof Commands (Sprint 1 P0)

**Tenant policy limits:**

```bash
cd /app/backend
pytest -q tests/test_tenant_policy_limits.py
```

**Money path E2E:**

```bash
cd /app/e2e
yarn test:e2e tests/money-path.spec.ts
```
