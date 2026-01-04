# Finance (EN)

**Menu path (UI):** Core → Finance  
**Frontend route:** `/finance`  
**Owner-only:** Yes (in menu config)  

---

## 1) Purpose and scope

Finance provides operator-facing views and actions for transaction monitoring, reconciliation, and risk investigation at the tenant level. It is used to diagnose balance mismatches, investigate suspicious transactions, and support operational finance workflows.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) primarily.
- Finance/Ops roles with owner-level privileges.
- Tenant admins typically do not have access.

---

## 3) Sub-sections / tabs

In the current UI (`frontend/src/pages/Finance.jsx`):
- Overview summary cards
- Transactions list
- Player risk/balance panels (implementation-dependent)

Backend surfaces are split:
- Core finance transactions (in `routes/core.py`): `GET /api/v1/finance/transactions`
- Advanced finance actions (in `routes/finance.py`): withdrawals review flow under `/api/v1/finance/*`

---

## 4) Core workflows (step-by-step)

### 4.1 View transactions
1) Open Finance.
2) Use filters (type/status/date range, if present).
3) Review amounts, states, and players.

**API calls (observed/expected):**
- List transactions: `GET /api/v1/finance/transactions?type=<...>&page=<n>&page_size=<n>`

### 4.2 Investigate a player from a transaction
1) Identify `player_id` from a transaction row.
2) Open Players and search by `player_id`.

### 4.3 Reconciliation view (if enabled)
- Reconciliation may be shown as summary cards or separate report.

---

## 5) Field guide (practical tips)

- Always capture **transaction id**, **player id**, **tenant**, and **time window**.
- For disputes, cross-check:
  - ledger changes
  - withdrawal states
  - payout attempts

**Do not:**
- Manually override balances without break-glass control.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Finance page shows “Network error” or loads nothing.
   - **Likely cause:** backend unreachable or auth invalid.
   - **Fix:** re-login; confirm backend is reachable; check DevTools Network.
   - **Verification:** `GET /api/v1/finance/transactions` returns 200.

2) **Symptom:** Transactions list is empty.
   - **Likely cause:** time window/filter too narrow; wrong tenant context.
   - **Fix:** widen filters; confirm tenant context.
   - **Verification:** list endpoint returns items.

3) **Symptom:** Balance mismatch reported by player.
   - **Likely cause:** pending withdrawals held balance; delayed ledger reconciliation.
   - **Fix:** check withdrawal state; check ledger balance endpoint (if available).
   - **Verification:** wallet ledger shows expected available/held after review.

4) **Symptom:** Totals differ between Finance and Reports.
   - **Likely cause:** timezone/aggregation differences; report caching.
   - **Fix:** compare same period boundaries/timezone; re-generate report.
   - **Verification:** totals reconcile within expected tolerance.

5) **Symptom:** Clicking a transaction fails with 404.
   - **Likely cause:** detail endpoint not implemented.
   - **Fix:** use the list row fields; escalate to backend if detail is required.
   - **Verification:** a transaction detail endpoint returns 200 (if implemented).

6) **Symptom:** Slow load / timeouts.
   - **Likely cause:** large date range.
   - **Fix:** narrow range; reduce page size.
   - **Verification:** response time improves.

7) **Symptom:** 403 Forbidden.
   - **Likely cause:** not platform owner / missing privilege.
   - **Fix:** use an owner admin; verify role.
   - **Verification:** calls succeed with correct role.

8) **Symptom:** Export missing.
   - **Likely cause:** export feature not available in this build.
   - **Fix:** use Reports export if available.
   - **Verification:** export files generated in Reports.

9) **Symptom:** Transaction status appears inconsistent.
   - **Likely cause:** async payout processing; state machine transitions.
   - **Fix:** check payout attempts and withdrawal review history.
   - **Verification:** state transitions follow expected path.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Transaction detail / drill-down actions return 404.
   - **Likely cause:** UI expects a transaction detail route not present in backend.
   - **Impact:** Admin cannot open deep transaction detail; must work with list data.
   - **Admin Workaround:** Use list row fields + player detail + withdrawal audit to investigate.
   - **Escalation Package:**
     - Method + path: capture from DevTools
     - Request sample: cURL export
     - Expected vs actual: expected 200, actual 404
     - Logs: search `finance` + transaction id
   - **Resolution Owner:** Backend
   - **Verification:** detail route returns 200 and UI drill-down works.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Transactions list loads and filters work.

### 8.2 System → Logs
- Look for finance endpoint errors.

### 8.3 App / container logs
- Search keywords:
  - `finance/transactions`
  - `TX_NOT_FOUND`
  - `tenant_id`

### 8.4 System → Audit Log
- Expected events (if implemented): finance-related actions, withdrawals review.

### 8.5 DB audit (if available)
- `transaction` table is the ground truth.
- `auditevent` should record finance actions.

---

## 9) Security notes + rollback

- Finance actions can be high-impact.
- Never modify balances outside audited flows.

---

## 10) Related links

- Withdrawals: `/docs/new/en/admin/core/withdrawals.md`
- Reports: `/docs/new/en/admin/system/reports.md`
- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
