# Approval Queue (EN)

**Menu path (UI):** Risk & Compliance → Approval Queue  
**Frontend route:** `/approvals`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Approval actions are high-risk; always record **who approved what and why**.
- For each decision:
  - capture request path + response (DevTools → Network)
  - verify **Audit Log** evidence (if implemented)
  - check **Logs** for failures
- If you cannot see pending items, confirm tenant context and backend filtering.

---

## 1) Purpose and scope

Approval Queue is the workflow engine for dual-control / compliance approvals.

In this build, UI is implemented in `frontend/src/pages/ApprovalQueue.jsx`.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin)
- Compliance / Finance approvers (if roles exist)

---

## 3) Sub-sections / tabs (as in UI)

ApprovalQueue.jsx tabs:
- Pending
- Approved
- Rejected
- Policies (rules)
- Delegations (coming soon)

---

## 4) Core workflows

### 4.1 View pending requests
1) Open Approval Queue.
2) Confirm **Pending** tab.

**API calls (as used by UI):**
- `GET /api/v1/approvals/requests?status=pending`

### 4.2 Approve / reject a request
1) Click a request.
2) Add a note.
3) Click Approve or Reject.

**API calls:**
- `POST /api/v1/approvals/requests/{id}/action` body `{ action: "approve"|"reject", note: "..." }`

---

## 5) Field guide (practical tips)

- Approvals should be tied to:
  - policy/rule
  - SLA
  - evidence pack (links, screenshots, logs)
- Use consistent rejection reasons.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Pending list always empty.
   - **Likely cause:** no requests exist; or backend filters incorrectly.
   - **Fix:** confirm seeding; confirm tenant_id filter.
   - **Verification:** GET returns rows.

2) **Symptom:** Approved/Rejected tabs still show Pending.
   - **Likely cause:** backend ignores `status` query param.
   - **Fix:** implement status filtering.
   - **Verification:** each tab shows its correct subset.

3) **Symptom:** Approve/Reject returns 422.
   - **Likely cause:** backend expects `action` as embedded field and doesn’t accept `note`.
   - **Fix:** align request body schema (or accept note).
   - **Verification:** action returns 200.

4) **Symptom:** Approve/Reject returns 404.
   - **Likely cause:** request id not found.
   - **Fix:** refresh list; retry.
   - **Verification:** item disappears from Pending.

5) **Symptom:** Delegations tab is “Coming Soon”.
   - **Likely cause:** feature not implemented.
   - **Fix:** treat as placeholder.
   - **Verification:** (future) endpoint exists.

6) **Symptom:** Policies tab fails with 404.
   - **Likely cause:** `/api/v1/approvals/rules` not implemented.
   - **Fix:** implement rules endpoint or hide tab.
   - **Verification:** policies list loads.

7) **Symptom:** 401/403 on approvals endpoints.
   - **Likely cause:** auth expired / insufficient permissions.
   - **Fix:** re-login; use owner role.
   - **Verification:** GET/POST return 200.

8) **Symptom:** No audit trail exists for approvals.
   - **Likely cause:** approvals actions are not audited.
   - **Fix:** add audit events for approve/reject.
   - **Verification:** **Audit Log** contains `approval.request.approved/rejected`.

9) **Symptom:** SLA tracking not visible.
   - **Likely cause:** backend model doesn’t store SLA metadata.
   - **Fix:** add fields; show in UI.
   - **Verification:** SLA shown and alerts on breach.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI requests status-based lists, but backend always returns pending.
   - **Likely Cause:** `backend/app/routes/approvals.py` hardcodes `status == "pending"`.
   - **Impact:** Approved/Rejected history views are incorrect.
   - **Admin Workaround:** none (UI cannot reliably review history).
   - **Escalation Package:**
     - `GET /api/v1/approvals/requests?status=approved`
     - expected: approved list; actual: pending list
     - keywords: `approvals/requests`
   - **Resolution Owner:** Backend
   - **Verification:** query param filters are respected.

2) **Symptom:** UI sends `{ action, note }` but backend accepts only embedded `action`.
   - **Likely Cause:** backend signature is `action: str = Body(..., embed=True)`.
   - **Impact:** Approve/Reject can 422 and become unusable.
   - **Admin Workaround:** none.
   - **Escalation Package:** capture 422 response body.
   - **Resolution Owner:** Backend
   - **Verification:** backend accepts UI body; note stored.

3) **Symptom:** Policies and Delegations endpoints are missing.
   - **Likely Cause:** `/api/v1/approvals/rules` and `/api/v1/approvals/delegations` not implemented.
   - **Impact:** incomplete approval governance.
   - **Admin Workaround:** maintain policies externally.
   - **Resolution Owner:** Backend/Product

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Approve/Reject moves items out of Pending.

### 8.2 System → Logs
- Check 4xx/5xx for approvals endpoints.

### 8.3 System → Audit Log
- Verify approval events exist (if implemented).

### 8.4 DB verification
- `approval_requests` rows show updated status.

---

## 9) Security notes

- Approval is a privileged action; enforce separation of duties.
- Always require a reason.

---

## 10) Related links

- Risk Rules: `/docs/new/en/admin/risk-compliance/risk-rules.md`
- Responsible Gaming: `/docs/new/en/admin/risk-compliance/responsible-gaming.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
