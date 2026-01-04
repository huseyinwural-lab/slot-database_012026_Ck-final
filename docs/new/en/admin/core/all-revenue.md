# All Revenue (EN)

**Menu path (UI):** Core → All Revenue  
**Frontend route:** `/owner-revenue`  
**Owner-only:** Yes  

---

## 1) Purpose and scope

All Revenue provides platform-wide revenue analytics across all tenants (GGR, bets, wins, transactions) within a time window. It is primarily used by platform owners for oversight, anomaly detection, and high-level reconciliation.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) only.

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/OwnerRevenue.jsx`):
- Date range selector
- Tenant filter (All tenants or single tenant)
- Summary cards
- Revenue by tenant breakdown table

---

## 4) Core workflows (step-by-step)

### 4.1 Change date range
1) Select a date range (24h / 7d / 30d / 90d).
2) Review the updated totals.

### 4.2 Filter to a single tenant
1) Select a tenant from the tenant dropdown.
2) Review totals and per-tenant line.

**API calls (observed from frontend):**
- Revenue (all tenants): `GET /api/v1/reports/revenue/all-tenants?from_date=<iso>&to_date=<iso>&tenant_id=<optional>`

---

## 5) Field guide (practical tips)

- Always confirm the selected time window and timezone assumptions.
- Use tenant filter to validate anomalies in a single tenant.
- For detailed reconciliation, cross-check with Finance and Reports.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Page shows “Failed to load revenue data”.
   - **Likely cause:** endpoint 404/500 or auth issue.
   - **Fix:** confirm platform owner role; check DevTools Network response.
   - **Verification:** revenue endpoint returns 200 and JSON includes totals.

2) **Symptom:** Values are all zeros.
   - **Likely cause:** no data in range; wrong tenant filter.
   - **Fix:** widen range; select All tenants.
   - **Verification:** totals change when range is widened.

3) **Symptom:** Tenant dropdown is empty.
   - **Likely cause:** backend returned empty tenants list in revenue payload.
   - **Fix:** confirm tenants exist; check Tenants list.
   - **Verification:** revenue response includes tenants array.

4) **Symptom:** Totals mismatch Finance.
   - **Likely cause:** aggregation definitions or timezone differences.
   - **Fix:** compare same period boundaries; confirm timezone.
   - **Verification:** reconcile within expected tolerance.

5) **Symptom:** Slow load.
   - **Likely cause:** large range aggregation.
   - **Fix:** reduce range; run off-peak.
   - **Verification:** response time decreases.

6) **Symptom:** Tenant filter does not change values.
   - **Likely cause:** UI not passing tenant_id, or backend ignoring tenant_id.
   - **Fix:** check request params; escalate to backend if ignored.
   - **Verification:** per-tenant selection changes totals.

7) **Symptom:** Unexpected negative GGR.
   - **Likely cause:** data anomalies, refunds/chargebacks.
   - **Fix:** drill into Finance transactions; check chargebacks.
   - **Verification:** underlying transactions explain the result.

8) **Symptom:** 403 Forbidden.
   - **Likely cause:** not platform owner.
   - **Fix:** use platform owner admin.
   - **Verification:** call succeeds with correct role.

9) **Symptom:** Cache/stale revenue.
   - **Likely cause:** cached summary not refreshed.
   - **Fix:** refresh; retry later.
   - **Verification:** values change with new `from_date/to_date` window.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Revenue endpoint returns 404 Not Found.
   - **Likely cause:** backend route missing for `/api/v1/reports/revenue/all-tenants`.
   - **Impact:** Platform-wide revenue view is blocked.
   - **Admin Workaround:** No admin-side workaround. Use Finance + tenant-level revenue as temporary alternative.
   - **Escalation Package:**
     - Method + path: `GET /api/v1/reports/revenue/all-tenants`
     - Request sample: query params `from_date`, `to_date`, optional `tenant_id`
     - Expected vs actual: expected 200; actual 404
     - Logs: search `revenue` / `reports/revenue` in backend logs
   - **Resolution Owner:** Backend
   - **Verification:** endpoint returns 200 and UI renders totals.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Date range changes update totals.
- Tenant filter updates totals.

### 8.2 System → Logs
- Look for 4xx/5xx around revenue endpoints.

### 8.3 App / container logs
- Search keywords:
  - `reports/revenue`
  - `tenant_id`

### 8.4 System → Audit Log
- Typically read-only; audit may not be emitted.

### 8.5 DB audit (if available)
- Aggregations should reconcile with `transaction` table.

---

## 9) Security notes + rollback

- Revenue dashboards expose sensitive business KPIs.
- Limit access to platform owners.

---

## 10) Related links

- Finance: `/docs/new/en/admin/core/finance.md`
- Reports: `/docs/new/en/admin/system/reports.md`
- Tenants: `/docs/new/en/admin/system/tenants.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
