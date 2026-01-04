# Audit Log (EN)

**Menu path (UI):** System → Audit Log  
**Frontend route:** `/audit`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- If a risky change occurred: immediately identify **who** (actor_user_id) and **what** (action + resource_id).
- Use **request_id** to correlate audit event → container logs.
- Export evidence (CSV) for incident ticket/post-mortem.
- If you cannot find an expected event: verify time range and check whether the action is audited in this build.

---

## 1) Purpose and scope

Audit Log is the immutable, queryable record of administrative actions. It is used for compliance evidence, incident forensics, and operational accountability.

---

## 2) Who uses this / permission requirements

- Platform Owner / Security / Compliance
- Engineering during incident response

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/AuditLog.jsx`):
- Filters (action, resource_type, status, actor_id, request_id, time range)
- Table view
- Export CSV
- Event details dialog (diff/before-after/raw)

**API calls (observed from frontend):**
- List: `GET /api/v1/audit/events?since_hours=<n>&limit=<n>&action=<...>&resource_type=<...>&status=<...>&actor_user_id=<...>&request_id=<...>`
- Export: `GET /api/v1/audit/export?since_hours=<n>`

Backend routes: `backend/app/routes/audit.py`

---

## 4) Core workflows (step-by-step)

### 4.1 Investigate a suspicious change
1) Set time range (start with Last 24 Hours).
2) Filter by **action** (if known) or **resource_type**.
3) Open the event details.
4) Copy `request_id` and correlate with backend logs.

### 4.2 Produce compliance evidence
1) Apply filters (time range + actor).
2) Click **Export CSV**.
3) Attach CSV to ticket/post-mortem.

---

## 5) Field guide (practical tips)

- Prefer filtering by **request_id** when you have it.
- Use “Before/After” and “Diff” for rapid review.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Audit events list is empty.
   - **Likely cause:** time range too narrow; no events.
   - **Fix:** increase since_hours; remove filters.
   - **Verification:** list endpoint returns items.

2) **Symptom:** Expected event is missing.
   - **Likely cause:** the action is not audited in this build.
   - **Fix:** use container logs as evidence; escalate to add auditing.
   - **Verification:** after implementation, action emits an audit event.

3) **Symptom:** Export fails.
   - **Likely cause:** backend export route failing or auth.
   - **Fix:** check `GET /api/v1/audit/export` response; retry with smaller time range.
   - **Verification:** CSV downloads.

4) **Symptom:** Diff is empty.
   - **Likely cause:** event did not include diff_json.
   - **Fix:** use raw JSON and before/after.
   - **Verification:** raw JSON contains details.

5) **Symptom:** 403 Forbidden.
   - **Likely cause:** not platform owner.
   - **Fix:** use owner admin.
   - **Verification:** endpoint returns 200.

6) **Symptom:** Request_id is missing.
   - **Likely cause:** legacy events.
   - **Fix:** correlate by timestamp + actor.
   - **Verification:** container log lines match timeframe.

7) **Symptom:** Audit shows DENIED events.
   - **Likely cause:** policy blocked the request.
   - **Fix:** validate permissions and tenant context; do not bypass without approval.
   - **Verification:** subsequent request succeeds with correct role.

8) **Symptom:** Too much noise.
   - **Likely cause:** broad filters.
   - **Fix:** filter by action/resource_type/actor.
   - **Verification:** relevant subset is visible.

9) **Symptom:** Timezone confusion on timestamps.
   - **Likely cause:** UI localizes timestamps.
   - **Fix:** rely on ISO timestamp in raw JSON.
   - **Verification:** consistent ordering and interpretation.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Export CSV returns an error or empty file.
   - **Likely Cause:** backend export route is present but may be tenant-scoped or filtered unexpectedly.
   - **Impact:** Evidence generation blocked.
   - **Admin Workaround:** Export smaller ranges; capture screenshots of event details as temporary evidence.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/audit/export`
     - Request sample: `since_hours=<n>`
     - Expected vs actual: expected CSV with events; actual error/empty
     - Logs keywords: `audit export`, `since_hours`
   - **Resolution Owner:** Backend
   - **Verification:** export downloads CSV with correct event count.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Filters work; events list updates.

### 8.2 System → Logs
- Use request_id to correlate audit → runtime logs.

### 8.3 App / container logs
- Search by `request_id`, `action`, `resource_id`.

### 8.4 DB audit (if available)
- Canonical table: `auditevent`.

---

## 9) Security notes + rollback

- Audit log is evidence; do not modify.

---

## 10) Related links

- Logs: `/docs/new/en/admin/system/logs.md`
- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
