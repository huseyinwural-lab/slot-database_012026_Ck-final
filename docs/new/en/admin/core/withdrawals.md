# Withdrawals (EN)

**Menu path (UI):** Core → Withdrawals  
**Frontend route:** `/withdrawals`  
**Owner-only:** Yes (in menu config)  

---

## 1) Purpose and scope

Withdrawals is the operator menu for reviewing, approving/rejecting, retrying, and marking withdrawals as paid. It is one of the most incident-prone operational areas.

---

## 2) Who uses this / permission requirements

- Platform Owner / Finance Ops (owner-level) only.

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/FinanceWithdrawals.jsx`):
- Filters (state, date_from/date_to, amount range, player id)
- Withdrawals table
- Actions:
  - Approve
  - Reject (with reason)
  - Retry payout
  - Mark paid

---

## 4) Core workflows (step-by-step)

### 4.1 Filter withdrawals
1) Open Withdrawals.
2) Set filters:
   - state
   - date range
   - amount min/max
   - player_id
3) Apply/refresh.

**API calls (backend supported):**
- List: `GET /api/v1/finance/withdrawals?state=<...>&limit=<n>&offset=<n>&player_id=<...>&date_from=<...>&date_to=<...>&min_amount=<...>&max_amount=<...>&sort=<...>`

### 4.2 Approve a withdrawal
1) Select a withdrawal with state `requested`.
2) Click **Approve**.
3) Provide a reason (recommended).

**API calls (backend supported):**
- Review: `POST /api/v1/finance/withdrawals/{tx_id}/review` body `{ action: "approve", reason }`

### 4.3 Reject a withdrawal
1) Select a withdrawal with state `requested`.
2) Click **Reject**.
3) Provide a reason.

**API calls:**
- Review: `POST /api/v1/finance/withdrawals/{tx_id}/review` body `{ action: "reject", reason }`

### 4.4 Retry a payout (stuck/failed)
1) Identify a withdrawal that is failed/stuck.
2) Click **Retry**.
3) Provide a reason (backend requires it).

**API calls (backend supported):**
- Retry: `POST /api/v1/finance-actions/withdrawals/{tx_id}/retry` body `{ reason }`

### 4.5 Mark withdrawal as paid
1) Confirm payment provider indicates the payout completed.
2) Click **Mark Paid**.
3) Provide a reason.

**API calls (backend supported):**
- Mark paid: `POST /api/v1/finance/withdrawals/{tx_id}/mark-paid` body `{ reason }`

---

## 5) Field guide (practical tips)

- Always capture: tx_id, player_id, amount, currency, state, provider.
- Approve only after KYC and risk checks are satisfied.
- Reject should roll back held funds to available (expected behavior).

**Do not:**
- Approve without documenting reason.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Withdrawal list does not load.
   - **Likely cause:** backend error or auth invalid.
   - **Fix:** verify owner role; check Network call to `/api/v1/finance/withdrawals`.
   - **Verification:** list endpoint returns items + meta.

2) **Symptom:** Approve fails with 400 INVALID_ACTION.
   - **Likely cause:** client sent unsupported action.
   - **Fix:** ensure action is `approve` or `reject`.
   - **Verification:** review call returns 200.

3) **Symptom:** Reject does not refund player (held not released).
   - **Likely cause:** ledger delta not applied due to error.
   - **Fix:** check backend logs; retry reject; escalate if ledger service failed.
   - **Verification:** player available increases and held decreases.

4) **Symptom:** Retry returns 400 “Reason is required”.
   - **Likely cause:** UI did not send reason.
   - **Fix:** include a reason and retry.
   - **Verification:** retry returns `retry_initiated`.

5) **Symptom:** Retry returns 422 PAYMENT_RETRY_LIMIT_EXCEEDED.
   - **Likely cause:** tenant policy retry limit reached.
   - **Fix:** stop retries; escalate to payments engineering; consider manual resolution.
   - **Verification:** audit event `FIN_PAYOUT_RETRY_BLOCKED` present.

6) **Symptom:** Retry returns 429 PAYMENT_COOLDOWN_ACTIVE.
   - **Likely cause:** cooldown window not elapsed.
   - **Fix:** wait remaining cooldown; retry once.
   - **Verification:** retry succeeds after cooldown.

7) **Symptom:** Mark Paid fails.
   - **Likely cause:** invalid state transition (not approved), or missing reason.
   - **Fix:** ensure withdrawal is approved; include reason.
   - **Verification:** transaction state becomes `paid`.

8) **Symptom:** Duplicate withdrawal request.
   - **Likely cause:** player retried during latency; idempotency not enforced.
   - **Fix:** identify duplicates; approve only one; reject others with reason.
   - **Verification:** only one payout attempt proceeds.

9) **Symptom:** Provider error / payout fails.
   - **Likely cause:** provider outage, invalid bank details, provider rejection.
   - **Fix:** check provider status; validate metadata; retry according to policy.
   - **Verification:** payout attempt status changes to submitted/paid.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI “Retry” succeeds but payout status does not change.
   - **Likely cause:** provider integration is mock/stub or async worker not running.
   - **Impact:** Withdrawal remains stuck; operational flow blocked.
   - **Admin Workaround:** If allowed, mark paid only after external confirmation; otherwise pause and escalate.
   - **Escalation Package:**
     - Method + path: `POST /api/v1/finance-actions/withdrawals/{tx_id}/retry`
     - Request sample: `{ "reason": "<text>" }`
     - Expected vs actual: expected `retry_initiated` + state progression; actual no progression
     - Logs: search `FIN_PAYOUT_RETRY_INITIATED`, `Adyen Payout Failed`, `provider error`, `attempt_id`
   - **Resolution Owner:** Backend / Payments
   - **Verification:** after retry, payout attempt transitions and withdrawal state updates.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- State transitions visible in the withdrawals table.

### 8.2 System → Logs
- Look for spikes in 4xx/5xx on finance-actions.

### 8.3 App / container logs
- Search keywords:
  - `FIN_WITHDRAW_APPROVED` / `FIN_WITHDRAW_REJECTED`
  - `FIN_PAYOUT_RETRY_INITIATED` / `FIN_PAYOUT_RETRY_BLOCKED`
  - `Adyen Payout Failed`

### 8.4 System → Audit Log
- Expected actions:
  - `FIN_WITHDRAW_APPROVED`
  - `FIN_WITHDRAW_REJECTED`
  - `FIN_PAYOUT_RETRY_INITIATED`

### 8.5 DB audit (if available)
- `transaction` row: `state`, `status`, `reviewed_by`, `reviewed_at`, `review_reason`.
- `payoutattempt` table: attempts by `withdraw_tx_id`.
- `auditevent` for evidence.

---

## 9) Security notes + rollback

- Withdrawals are high-risk. Never approve without evidence.
- Rollback:
  - If approved by mistake and not yet paid: reject if policy permits and refund held funds.
  - If already paid: treat as incident and follow chargeback/dispute procedures.

---

## 10) Related links

- KYC: `/docs/new/en/admin/operations/kyc-verification.md`
- Risk Rules: `/docs/new/en/admin/risk-compliance/risk-rules.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
