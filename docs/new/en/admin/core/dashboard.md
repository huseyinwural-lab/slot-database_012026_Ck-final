# Dashboard (EN)

**Menu path (UI):** Core → Dashboard  
**Frontend route:** `/dashboard`  
**Owner-only:** No  

---

## Ops Checklist (read first)

- Confirm tenant context + time range.
- If KPI looks off: immediately cross-check the source menu (Finance/Players/Games).

---

## 1) Purpose and scope

The Dashboard provides a top-level snapshot of platform/tenant performance: KPIs, time-series trends, and recent activity. It is intended for quick situational awareness and to help operators decide which deep-dive menu to open next.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin): can view across tenants (when tenant context is selected).
- Tenant Admin / Ops: monitors tenant KPIs and operational health.
- Finance/Risk: uses dashboard signals to decide on deeper investigation.

---

## 3) Sub-sections (if applicable)

Typical sections:
- KPI cards (counts/amounts)
- Charts (trends)
- Recent activity table (if enabled)

---

## 4) Core workflows

### 4.1 Change time range
1) Select a date range / preset.
2) Observe KPI and chart refresh.

### 4.2 Filter by tenant (platform owner)
1) Switch tenant context.
2) Re-check KPI values match the intended tenant.

### 4.3 Export (if available)
- Some deployments expose export per widget; others do not.

---

## 5) Field guide (practical tips)

- Expect **data latency**: some metrics are eventually consistent.
- If a single KPI looks off, cross-check the source menu:
  - Deposits/withdrawals → Finance / Withdrawals
  - Player changes → Players
  - Game activity → Games

**When not to use this menu:**
- For case-level resolution. Use Dashboard only to identify where to investigate.

---

## 6) Common errors (symptom → likely cause)

1) **Symptom:** Dashboard is empty / shows zeros
   - Likely cause: wrong tenant context, no data in selected time window, or backend API not reachable.

2) **Symptom:** KPI values don’t match reports
   - Likely cause: timezone mismatch, different aggregation windows, or delayed ETL.

3) **Symptom:** Charts not loading but page renders
   - Likely cause: one widget API failing while others succeed.

4) **Symptom:** Slow load / timeouts
   - Likely cause: large time window or heavy aggregation.

---

## 7) Resolution steps (step-by-step)

1) Confirm tenant context and time range.
2) Refresh and check browser DevTools → Network for failing calls.
3) If a single endpoint fails, copy status code and request path and check backend logs.
4) Try a smaller time range.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Values change after time-range updates.
- Cross-check against the relevant deep-dive menus.

### 8.2 App / container logs
- Search by endpoint path and timeframe.
- If available, correlate by `x-request-id`.

### 8.3 Audit log
- Dashboard is typically read-only; no audit event expected.

### 8.4 Database verification (if applicable)
- Not typically required for dashboard view issues.

---

## 9) Security notes

- Dashboard may expose sensitive financial KPIs; restrict access to authorized roles.

---

## 10) Related links

- `/docs/new/en/admin/core/players.md`
- `/docs/new/en/admin/core/finance.md`
- `/docs/new/en/admin/system/reports.md`
- `/docs/new/en/guides/common-errors.md`
