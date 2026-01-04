# KYC Verification (EN)

**Menu path (UI):** Operations → KYC Verification  
**Frontend route:** `/kyc`  
**Feature flag (UI):** `can_manage_kyc`  

---

## Ops Checklist (read first)

- Confirm tenant context; KYC decisions are player-impacting and legally sensitive.
- Always record:
  - decision (approve/reject)
  - reason
  - evidence references
- Verify outcomes in:
  - **UI** (queue state)
  - **Audit Log** (if implemented)
  - **Logs** (4xx/5xx / request_id)

---

## 1) Purpose and scope

KYC Verification manages identity verification workflow:
- queue of pending verifications
- document review outcomes
- operational KPIs (pending/verified/rejected)

Frontend implementation: `frontend/src/pages/KYCManagement.jsx`.

> Important: backend `/api/v1/kyc/*` in this repo is explicitly labeled **MOCKED UI support** and may be disabled in prod/staging.

---

## 2) Who uses this / permission requirements

- Support / KYC Ops
- Compliance

Access control:
- UI requires `can_manage_kyc` (see menu config)
- backend checks `feature_required("can_manage_kyc")`

---

## 3) Sub-sections / functional areas

KYCManagement UI:
- KPI cards (dashboard)
- Verification queue
- Review modal (documents)

---

## 4) Core workflows

### 4.1 View KYC dashboard
1) Open Operations → KYC Verification.
2) Observe KPIs.

**API calls (from UI):**
- `GET /api/v1/kyc/dashboard`

### 4.2 View verification queue
1) Open the Queue view.

**API calls:**
- `GET /api/v1/kyc/queue`

### 4.3 Review a document
1) Open a queue item.
2) Review documents.
3) Choose status:
   - approved
   - rejected
4) Submit.

**API calls:**
- `POST /api/v1/kyc/documents/{doc_id}/review`

---

## 5) Operational notes

- Enforce dual-control for high-risk players (policy dependent).
- Keep PII exposure minimal.
- Always verify the player’s final `kyc_status` is consistent across player profile and queue.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** KYC menu is not visible.
   - **Likely cause:** missing `can_manage_kyc` capability.
   - **Fix:** assign feature to role/tenant.
   - **Verification:** menu appears; route loads.

2) **Symptom:** Dashboard/queue endpoints return 404.
   - **Likely cause:** KYC mock guard disabled in the environment.
   - **Fix:** enable mock only in dev/test; implement real KYC service for staging/prod.
   - **Verification:** endpoints return 200.

3) **Symptom:** Queue is empty while there are pending players.
   - **Likely cause:** backend filtering mismatch (`kyc_status == pending`) or tenant mismatch.
   - **Fix:** verify tenant_id filter; confirm player records.
   - **Verification:** queue returns players.

4) **Symptom:** Document images show placeholders.
   - **Likely cause:** MOCK document URLs.
   - **Fix:** integrate real document storage.
   - **Verification:** real document URLs load.

5) **Symptom:** Review submit returns 422.
   - **Likely cause:** payload schema mismatch.
   - **Fix:** ensure body contains `status` with values `approved|rejected`.
   - **Verification:** response shows updated status.

6) **Symptom:** Review submit returns 404 for player.
   - **Likely cause:** mock doc_id does not map to real player_id.
   - **Fix:** implement proper KYC document model.
   - **Verification:** review updates the intended player.

7) **Symptom:** Approved player still appears in pending queue.
   - **Likely cause:** status not persisted or cache.
   - **Fix:** verify DB commit; refresh.
   - **Verification:** player disappears from pending.

8) **Symptom:** No audit trail for approve/reject.
   - **Likely cause:** audit logging not implemented for KYC endpoints.
   - **Fix:** add audit events for KYC decisions.
   - **Verification:** Audit Log contains `kyc.review.approved/rejected`.

9) **Symptom:** KYC decisions conflict with jurisdiction rules.
   - **Likely cause:** missing compliance policy enforcement.
   - **Fix:** add policy checks; route through Approval Queue.
   - **Verification:** policy violations are blocked and logged.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** KYC appears functional in dev, but disappears in staging/prod.
   - **Likely Cause:** `backend/app/routes/kyc.py` is explicitly **MOCKED** and guarded by environment flags.
   - **Impact:** No production-grade KYC workflow.
   - **Admin Workaround:** None.
   - **Escalation Package:** define real provider integration and data model.
   - **Resolution Owner:** Backend/Product

2) **Symptom:** Document storage is placeholder.
   - **Likely Cause:** no document table/storage.
   - **Impact:** cannot review real documents.
   - **Resolution Owner:** Backend

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Dashboard counts update after a review.
- Queue moves player out of pending when approved/rejected.

### 8.2 System → Logs
- Check `/api/v1/kyc/*` for errors.

### 8.3 System → Audit Log
- Verify KYC review events exist (if implemented).

### 8.4 DB verification
- Player.kyc_status changes.

---

## 9) Security notes + rollback

- Never export raw document images outside approved tools.
- Rollback is typically not applicable; instead open a new review with proper approval.

---

## 10) Related links

- Players: `/docs/new/en/admin/core/players.md`
- Approval Queue: `/docs/new/en/admin/risk-compliance/approval-queue.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
