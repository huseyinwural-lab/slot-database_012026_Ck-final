# Logs (EN)

**Menu path (UI):** System → Logs  
**Frontend route:** `/system/logs`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Identify the incident category first: **errors**, **deployments**, **db**, **cache**, **queues**, or generic **events**.
- Always capture a **time window** and correlate to a **request path** (and `x-request-id` if available).
- Validate the impact in UI (affected menu) and confirm evidence in **Audit Log** when a change was made.
- If the UI category is empty, check whether the backend endpoint is stubbed (see gaps) and pivot to container logs.

---

## 1) Purpose and scope

System Logs provides an operator-facing window into system event records and operational categories (cron, deployments, config changes, error logs, queues/workers, DB/cache, and archive). It is used for first-response triage, correlation, and evidence gathering.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) / Ops
- Support & Engineering during incidents (if granted)

---

## 3) Sub-sections / categories

In the current UI (`frontend/src/pages/SystemLogs.jsx`), categories map to endpoints:
- System Events → `GET /api/v1/logs/events`
- Cron Jobs → `GET /api/v1/logs/cron`
- Service Health → `GET /api/v1/logs/health`
- Deployments → `GET /api/v1/logs/deployments`
- Config Changes → `GET /api/v1/logs/config`
- Error Logs → `GET /api/v1/logs/errors`
- Queue / Workers → `GET /api/v1/logs/queues`
- Database Logs → `GET /api/v1/logs/db`
- Cache Logs → `GET /api/v1/logs/cache`
- Log Archive → `GET /api/v1/logs/archive`

---

## 4) Core workflows (step-by-step)

### 4.1 Triage an incident
1) Open Logs.
2) Start with **Error Logs** and **System Events**.
3) Expand into category relevant to the symptom:
   - Deployment regressions → Deployments
   - Slow queries/timeouts → DB
   - Stale configs → Cache / Config Changes

### 4.2 Collect an escalation package
1) Record the timestamp range.
2) Copy the log row JSON.
3) Capture affected API endpoint and status code from DevTools.
4) Include the tenant context if applicable.

---

## 5) Field guide (practical tips)

- Use Logs for **what happened**, and Audit Log for **who changed what**.
- If Logs are empty for a category, it may be unimplemented/stubbed.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Logs table shows “No logs found for this category.”
   - **Likely cause:** no events in range, or backend endpoint returns empty list.
   - **Fix:** switch to System Events; widen time window; confirm backend route behavior.
   - **Verification:** `GET /api/v1/logs/<category>` returns rows.

2) **Symptom:** Logs load but fields are missing/odd.
   - **Likely cause:** inconsistent schema across categories.
   - **Fix:** rely on raw JSON fields and timestamps; escalate for schema normalization.
   - **Verification:** consistent keys across events.

3) **Symptom:** Error Logs are empty during an incident.
   - **Likely cause:** errors are not ingested into this UI category.
   - **Fix:** pivot to container logs.
   - **Verification:** container logs show stack traces/timeouts.

4) **Symptom:** Slow UI when opening Logs.
   - **Likely cause:** large payload / heavy table render.
   - **Fix:** refresh; use narrower time; prefer container logs for deep analysis.
   - **Verification:** load time improves.

5) **Symptom:** 403 Forbidden on logs endpoints.
   - **Likely cause:** user is not platform owner.
   - **Fix:** use an owner admin.
   - **Verification:** endpoints return 200.

6) **Symptom:** Cron tab shows no actionable info.
   - **Likely cause:** cron endpoints are stubbed.
   - **Fix:** check job runner/worker logs in container.
   - **Verification:** cron job starts and emits events.

7) **Symptom:** Deployments tab doesn’t show the latest deployment.
   - **Likely cause:** deployments endpoint is stubbed.
   - **Fix:** use your deployment system logs.
   - **Verification:** a deployment record appears.

8) **Symptom:** DB/Cache tabs do not correlate with the issue.
   - **Likely cause:** these categories are stubbed or not wired.
   - **Fix:** use infra-level monitoring and container logs.
   - **Verification:** DB/cache events observable.

9) **Symptom:** Trace View shows “Coming Soon”.
   - **Likely cause:** feature not implemented.
   - **Fix:** use request_id correlation in logs.
   - **Verification:** (future) distributed tracing UI exists.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Most categories return empty lists.
   - **Likely Cause:** backend `routes/logs.py` implements `/events` but returns empty arrays for many category endpoints.
   - **Impact:** Admin cannot rely on category tabs for evidence; must use container logs for deep incidents.
   - **Admin Workaround:**
     - Use **System Events** tab as primary.
     - Use container logs for cron/deployments/db/cache details.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/logs/<category>` (cron/health/deployments/config/errors/queues/db/cache/archive)
     - Expected vs actual: expected meaningful events; actual `[]`
     - Logs keywords: `logs/<category>`
   - **Resolution Owner:** Backend
   - **Verification:** Each category endpoint returns non-empty event schema when events exist.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Switching tabs changes the dataset.

### 8.2 System → Audit Log
- For configuration changes, validate the corresponding audit event exists.

### 8.3 App / container logs
- Search by request path + timeframe.

### 8.4 DB audit (if available)
- `auditlog` / `auditevent` records should align with incidents.

---

## 9) Security notes + rollback

- Logs may contain sensitive data; restrict access.

---

## 10) Related links

- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
