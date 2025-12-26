# Sprint A: Core Hardening & Automation - Task Order

**Status:** ACTIVE
**Goal:** Automate financial hygiene, close security gaps, and enable compliance ops.

---

## 1. P0-08: Velocity Engine (Rate Limiting Logic)
**Objective:** Prevent transaction spamming (e.g., 50 withdraw requests/min).

*   **Task 1.1:** Add `MAX_TX_VELOCITY` to `config.py`.
*   **Task 1.2:** Implement `check_velocity_limit` in `tenant_policy_enforcement.py`.
    *   Query: Count transactions for user in last `window` minutes.
*   **Task 1.3:** Integrate into `player_wallet.py` (Deposit/Withdraw routes).

## 2. P0-03: Withdraw Expiry Automation
**Objective:** Release funds locked in "Requested" state forever.

*   **Task 2.1:** Create `scripts/process_withdraw_expiry.py`.
    *   Find `requested` txs older than 24h.
    *   Loop:
        *   Call Ledger to refund (Held->Avail).
        *   Update Tx State -> `expired`.
        *   Log Audit.

## 3. P0-07: Chargeback Handler
**Objective:** Handle "Forced Refund" events safely.

*   **Task 3.1:** Create/Update endpoint `POST /api/v1/finance/chargeback`.
*   **Task 3.2:** Implement Ledger Logic (Force Debit).
    *   Allow negative balance.
    *   Update Tx State -> `chargeback`.

## 4. P0-13/14: Compliance UI
**Objective:** Connect backend logic to Frontend buttons.

*   **Task 4.1:** Admin UI - KYC Approval Button.
*   **Task 4.2:** Player UI - Self-Exclusion Button.

---

**Execution Start:** Immediate.
**Owner:** E1 Agent.
