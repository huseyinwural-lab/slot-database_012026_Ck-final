# Support (EN)

**Menu path (UI):** Operations → Support  
**Frontend route:** `/support`  

---

## Ops Checklist (read first)

- Support work is a closed loop: ticket → action → evidence → resolution.
- Always capture Request ID (Diagnostics) when you see a platform issue.
- Validate the backend endpoints for each tab; several are currently missing.

---

## 1) Purpose and scope

Support Center is the operations console for:
- ticket handling
- player chat sessions
- knowledge base
- canned responses
- diagnostics (last captured Request ID)

Frontend: `frontend/src/pages/Support.jsx`.

---

## 2) Who uses this / permission requirements

- Support agents
- Ops/Engineering for diagnostics

---

## 3) Sub-sections / tabs (UI)

Support.jsx tabs:
- Overview (dashboard + diagnostics)
- Inbox (tickets)
- Live Chat (sessions)
- Help Center (KB)
- Config (canned responses + automations placeholder)

---

## 4) Core workflows

### 4.1 Diagnostics: capture last Request ID
1) Open Support → Overview.
2) Copy Request ID.
3) Share to Ops for log correlation.

**Data source:** local storage / interceptor via `supportDiagnostics`.

### 4.2 View ticket queue
1) Open Inbox.
2) Select a ticket.

**API calls (as used by UI):**
- `GET /api/v1/support/tickets`

### 4.3 Reply to a ticket
1) Select ticket.
2) Write reply.
3) Click Reply.

**API calls (as used by UI):**
- `POST /api/v1/support/tickets/{ticket_id}/message`

---

## 5) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Overview dashboard never loads.
   - **Likely cause:** `GET /api/v1/support/dashboard` is missing.
   - **Fix:** implement dashboard endpoint or hide widget.
   - **Verification:** dashboard KPIs render.

2) **Symptom:** Inbox list loads but replying fails with 404.
   - **Likely cause:** backend route mismatch: backend implements `/tickets/{id}/reply`, UI calls `/tickets/{id}/message`.
   - **Fix:** align backend to accept `/message` or update UI.
   - **Verification:** reply persists and ticket status updates.

3) **Symptom:** Tickets list is empty in production.
   - **Likely cause:** no tickets exist or tenant filter mismatch.
   - **Fix:** seed a ticket; confirm tenant_id filtering.
   - **Verification:** GET returns list.

4) **Symptom:** Live Chat tab always empty.
   - **Likely cause:** `GET /api/v1/support/chats` not implemented.
   - **Fix:** implement chat sessions endpoint.
   - **Verification:** sessions render.

5) **Symptom:** KB tab always empty.
   - **Likely cause:** `GET /api/v1/support/kb` not implemented.
   - **Fix:** implement KB endpoints.
   - **Verification:** KB list renders.

6) **Symptom:** Config tab (canned responses) fails.
   - **Likely cause:** `GET/POST /api/v1/support/canned` not implemented.
   - **Fix:** implement canned response endpoints.
   - **Verification:** canned responses list updates.

7) **Symptom:** Reply succeeds but no audit evidence.
   - **Likely cause:** support routes not audited.
   - **Fix:** add audit events for messages.
   - **Verification:** Audit Log contains `support.ticket.replied`.

8) **Symptom:** Request ID is missing.
   - **Likely cause:** interceptor not capturing last error.
   - **Fix:** verify axios interceptor emits `support:last_error` and stores `support_last_error`.
   - **Verification:** Request ID appears after an error.

9) **Symptom:** 401/403 on support endpoints.
   - **Likely cause:** auth expired / permissions.
   - **Fix:** re-login; assign support role.
   - **Verification:** endpoints return 200.

---

## 6) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI uses `/dashboard`, `/chats`, `/kb`, `/canned` routes, but backend only implements `/tickets` and `/tickets/{id}/reply`.
   - **Likely Cause:** `backend/app/routes/support.py` is incomplete.
   - **Impact:** most Support Center tabs do not work.
   - **Admin Workaround:** use external ticketing system; rely on diagnostics + Logs for incident triage.
   - **Escalation Package:**
     - Missing endpoints:
       - `GET /api/v1/support/dashboard`
       - `GET /api/v1/support/chats`
       - `GET /api/v1/support/kb`
       - `GET /api/v1/support/canned`
       - `POST /api/v1/support/canned`
       - `POST /api/v1/support/tickets/{id}/message` (or align to `/reply`)
     - Keywords: `support/`
   - **Resolution Owner:** Backend

---

## 7) Verification (UI + Logs + Audit)

### 7.1 UI
- Ticket list shows.
- Reply adds a message.

### 7.2 System → Logs
- Search `support` endpoints errors.

### 7.3 System → Audit Log
- Verify support actions (if implemented).

---

## 8) Security notes

- Support notes may contain PII; apply redaction.
- Restrict access by role.

---

## 9) Related links

- Logs: `/docs/new/en/admin/system/logs.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
