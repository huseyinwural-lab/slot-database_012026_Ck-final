# Integrity Guards Specification

**Objective:** Implement "Double Lock" strategy (Service Level + Database Level) to guarantee data integrity.

## 1. Database Constraints (Hard Guards)

### 1.1 Uniqueness (Idempotency)
Table: `pricing_ledger` / `transactions`
- **Constraint:** `UNIQUE (tenant_id, listing_id, idempotency_key)`
- **Purpose:** Prevents double-spending or double-allocation even if service logic fails or retries aggressively.

### 1.2 Invariants (Negative Balance Protection)
Table: `quotas` / `balances`
- **Constraint:** `CHECK (balance >= 0)` or `CHECK (paid_units >= 0)`
- **Purpose:** Rejects any transaction that would result in a negative state, regardless of race conditions.

### 1.3 Referential Integrity
- **Constraint:** `FOREIGN KEY (pricing_policy_id)`
- **Purpose:** Ensures no transaction is linked to a non-existent or deleted policy.

## 2. Service Level Invariants (Soft Guards)

### 2.1 Pre-Computation Check
- **Logic:** Before attempting DB write, calculate `current_balance - requested_amount`.
- **Action:** If result < 0, throw `InsufficientBalanceError` immediately (save DB round-trip).

### 2.2 Frozen State
- **Logic:** If a listing/tenant is `FROZEN` or `SUSPENDED`, reject `pricing_commit` actions at the gateway.

## 3. Drift Detection
- **Mechanism:** Background job to sum `ledger_entries` and compare with `current_balance` snapshot.
- **Alert:** If `SUM(entries) != snapshot`, trigger P0 Alert.
