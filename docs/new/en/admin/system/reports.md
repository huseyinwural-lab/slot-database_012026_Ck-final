# Reports (EN)

**Menu path (UI):** System → Reports  
**Frontend route:** `/reports`  
**Owner-only:** Mixed (depends on tenant feature `can_view_reports`)  

---

## 1) Purpose and scope

Reports provides aggregated operational and financial views (overview KPIs, tables, exports). It is used for decision support, reconciliation, and evidence generation.

---

## 2) Who uses this / permission requirements

- Platform Owner: can access reports across tenants (depending on tenant context and entitlements).
- Tenant Admin / Finance: uses tenant reports if `can_view_reports` is enabled.
- Support/Risk: may use operational/risk reports.

---

## 3) Sub-sections / tabs

In the current UI (`frontend/src/pages/Reports.jsx`), navigation includes:
- Overview
- Real-Time (UI placeholder)
- Financial
- Players (LTV)
- Games
- Providers
- Bonuses
- Affiliates
- CRM
- CMS
- Operational
- Custom Builder (UI placeholder)
- Scheduled
- Export Center

Observed endpoints selected by tab:
- `GET /api/v1/reports/overview`
- `GET /api/v1/reports/financial`
- `GET /api/v1/reports/players/ltv`
- `GET /api/v1/reports/games`
- `GET /api/v1/reports/providers`
- `GET /api/v1/reports/bonuses`
- `GET /api/v1/reports/affiliates`
- `GET /api/v1/reports/risk`
- `GET /api/v1/reports/rg`
- `GET /api/v1/reports/kyc`
- `GET /api/v1/reports/crm`
- `GET /api/v1/reports/cms`
- `GET /api/v1/reports/operational`
- `GET /api/v1/reports/schedules`
- `GET /api/v1/reports/exports`

**Important implementation note:** the backend currently contains a stub `routes/reports.py` and a partial `routes/revenue.py` (revenue endpoints). Many of the listed report endpoints may return **404 Not Found** until implemented.

---

## 4) Core workflows

### 4.1 Generate a report view
1) Open Reports.
2) Select a report type from left navigation.
3) Wait for data to load.

**API calls:**
- `GET /api/v1/reports/<tab-specific-endpoint>`

### 4.2 Export
1) Select a report tab.
2) Click **Export**.

**API calls (observed from frontend):**
- Create export job: `POST /api/v1/reports/exports` body `{ type, requested_by }`

### 4.3 Cross-check / validation
- Validate financial reports against Finance ledger/transactions.
- Validate player reports against Players list.

---

## 5) Field guide (practical tips)

- Always record the **time window** and **timezone**.
- Prefer smaller time ranges to avoid timeouts.
- If totals look inconsistent, confirm whether the report is:
  - cached snapshot
  - live aggregation

**When not to use:**
- For case-level truth without cross-check (always cross-check with source-of-truth tables/menus).

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum 8 items.

1) **Symptom:** Report is empty
   - Likely cause: filters/time window; tenant context mismatch.
   - Fix: widen date range; confirm correct tenant context.
   - Verification: endpoint returns rows and UI table is populated.

2) **Symptom:** Report is very slow / times out
   - Likely cause: large range; heavy aggregation.
   - Fix: reduce the time range; run off-peak.
   - Verification: request duration drops and completes.

3) **Symptom:** Export does not download
   - Likely cause: browser pop-up/security; export is async.
   - Fix: check Export Center tab; allow downloads.
   - Verification: export file appears and is downloadable.

4) **Symptom:** Report totals mismatch Finance
   - Likely cause: timezone; different aggregation definitions; delayed ETL.
   - Fix: confirm timezone; compare same period boundaries; check latency.
   - Verification: reconciled totals within expected tolerance.

5) **Symptom:** Duplicate entries
   - Likely cause: aggregation bug or grouping keys.
   - Fix: narrow the report; compare with raw transactions.
   - Verification: duplicates disappear after fix or are explained by grouping.

6) **Symptom:** 403 Forbidden
   - Likely cause: missing tenant feature `can_view_reports` or role restriction.
   - Fix: enable feature for tenant; verify role permissions.
   - Verification: tab loads after entitlement update.

7) **Symptom:** 404 Not Found on report endpoints
   - Likely cause: backend endpoints not implemented in this build.
   - Fix: confirm backend release supports report endpoints.
   - Verification: endpoint exists and returns data.

8) **Symptom:** Scheduled reports not sending
   - Likely cause: scheduler/worker down; email integration missing.
   - Fix: check job runner; check mailer integration.
   - Verification: schedule job logs show success and recipients receive output.

9) **Symptom:** Cache/stale data
   - Likely cause: report caching.
   - Fix: refresh cache or regenerate.
   - Verification: “generated_at” changes and values update.

---

## 7) Resolution steps (step-by-step)

1) Capture failing endpoint + status code.
2) Confirm tenant context and entitlements.
3) Reduce time window.
4) Cross-check against source menus (Finance/Players/Games).
5) Collect evidence via logs/audit.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Confirm tab content loads.
- Confirm export job is created and visible in Export Center.

### 8.2 System → Logs
- Look for report request errors and slow queries.

### 8.3 App / container logs
- Search keywords:
  - `reports`
  - `exports`
  - `timeout`

### 8.4 System → Audit Log
- Expected audit events (if implemented):
  - `report.exported`
  - `report.generated`

### 8.5 Database audit (if present)
- Evidence table names are deployment-specific.
- For financial accuracy, use `transaction`/ledger tables as ground truth.

---

## 9) Security notes + rollback

- Reports can contain sensitive financial and personal data.
- Export files must be protected and time-bounded.
- If a report leaks data: revoke access, rotate secrets, and produce audit evidence.

---

## 10) Related links

- Finance: `/docs/new/en/admin/core/finance.md`
- Players: `/docs/new/en/admin/core/players.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
