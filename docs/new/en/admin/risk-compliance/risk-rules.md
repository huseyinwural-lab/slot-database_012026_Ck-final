# Risk Rules (EN)

**Menu path (UI):** Risk & Compliance → Risk Rules  
**Frontend route:** `/risk`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Confirm you are in the correct **tenant context** before creating/enabling rules.
- For any rule change, capture:
  - failing request URL + status code (DevTools → Network)
  - evidence in **Audit Log** (if implemented)
  - runtime failures in **Logs**
- Treat rule creation/toggles as production-impacting; plan rollback.

---

## 1) Purpose and scope

Risk Rules is the control plane for automated risk scoring and fraud detection. Rules typically:
- add/subtract risk score
- trigger cases/alerts
- gate actions (withdrawal payout, bonus issuance, RTP changes)

In this build, UI is implemented in `frontend/src/pages/RiskManagement.jsx` (Rules tab).

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) / Risk Ops
- Fraud / Compliance analysts (if roles are implemented)

> UI visibility: `frontend/src/config/menu.js` marks this menu as owner-only.

---

## 3) Sub-sections / tabs (as in UI)

`RiskManagement.jsx` provides a multi-tab “Risk & Fraud Engine” console:
- Overview (dashboard)
- Live Alerts
- Cases
- Investigation (evidence/notes)
- Rules
- Velocity
- (UI-only tabs) Payment / IP & Geo / Bonus Abuse / Logic

This page documents **Rules** primarily.

---

## 4) Core workflows (step-by-step)

### 4.1 List rules
1) Open Risk & Compliance → Risk Rules.
2) Switch to the **Rules** tab.

**API calls (as used by UI):**
- `GET /api/v1/risk/rules`

### 4.2 Create a rule
1) Click **Add Rule**.
2) Fill:
   - name
   - category (`account` / `payment` / `bonus_abuse`)
   - severity
   - score_impact
3) Click **Save Rule**.

**API calls:**
- `POST /api/v1/risk/rules`

### 4.3 Enable/disable (toggle) a rule
1) In the rules table, click **Activate/Pause**.

**API calls:**
- `POST /api/v1/risk/rules/{id}/toggle`

---

## 5) Field guide (practical tips)

- Prefer fewer, high-signal rules.
- Roll out changes gradually:
  - enable in “observe only” mode first (if implemented)
  - then switch to enforcement
- Always record a rationale and rollback condition in your ops notes.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Risk Rules page loads but Rules tab is empty.
   - **Likely cause:** no rules exist yet for the tenant.
   - **Fix:** create a rule; or confirm tenant context.
   - **Verification:** GET returns a list.

2) **Symptom:** Rules tab fails with 401.
   - **Likely cause:** admin session expired.
   - **Fix:** re-login.
   - **Verification:** GET returns 200.

3) **Symptom:** Rules tab fails with 403.
   - **Likely cause:** user is not platform owner.
   - **Fix:** use owner admin.
   - **Verification:** endpoint returns 200.

4) **Symptom:** Create Rule fails with 404.
   - **Likely cause:** backend `POST /api/v1/risk/rules` not implemented.
   - **Fix:** implement POST route or hide creation in UI.
   - **Verification:** POST returns 201 and list updates.

5) **Symptom:** Toggle fails with 404.
   - **Likely cause:** backend `POST /api/v1/risk/rules/{id}/toggle` not implemented.
   - **Fix:** implement toggle route.
   - **Verification:** rule status changes and persists after refresh.

6) **Symptom:** Create fails with 422.
   - **Likely cause:** schema mismatch (field names/types).
   - **Fix:** align request body (e.g., `score_impact` numeric).
   - **Verification:** POST accepted.

7) **Symptom:** Rule changes have no operational effect.
   - **Likely cause:** rules are stored but not enforced by runtime pipeline.
   - **Fix:** verify enforcement integration; check Logs for rule evaluation.
   - **Verification:** alerts/cases change when conditions are met.

8) **Symptom:** No audit evidence exists for rule changes.
   - **Likely cause:** risk endpoints are not audited.
   - **Fix:** add auditing; as interim, keep change tickets.
   - **Verification:** **Audit Log** shows `risk.rule.created/updated/toggled`.

9) **Symptom:** UI shows additional tabs (Payment/Geo/Bonus) but they never load data.
   - **Likely cause:** backend endpoints for those tabs are missing.
   - **Fix:** document as gaps; implement endpoints.
   - **Verification:** tabs populate.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI calls multiple risk endpoints, but backend only provides `GET /api/v1/risk/rules`.
   - **Likely Cause:** `backend/app/routes/risk.py` implements only `GET /rules` in this build.
   - **Impact:** Most Risk Engine tabs (dashboard/alerts/cases/velocity/blacklist/evidence) cannot function.
   - **Admin Workaround:** None. Use manual incident triage with Logs.
   - **Escalation Package:**
     - Expected endpoints (as called by UI):
       - `GET /api/v1/risk/dashboard`
       - `GET /api/v1/risk/alerts`
       - `GET /api/v1/risk/cases`
       - `PUT /api/v1/risk/cases/{id}/status`
       - `GET /api/v1/risk/velocity`
       - `GET/POST /api/v1/risk/blacklist`
       - `GET/POST /api/v1/risk/evidence`
     - Keywords: `risk/`
   - **Resolution Owner:** Backend
   - **Verification:** Each endpoint returns 200 and UI tabs show data.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Rule appears in list.
- Toggle persists after refresh.

### 8.2 System → Logs
- Check Error Logs for 4xx/5xx on `/api/v1/risk/*`.

### 8.3 System → Audit Log
- Verify rule create/toggle events exist (if auditing implemented).

### 8.4 DB verification
- `risk_rules` rows exist for the tenant.

---

## 9) Security notes + rollback

- Rules can block/allow financial actions.
- Rollback strategy:
  - disable the latest rule
  - verify the symptom stops
  - produce evidence package (Logs + Audit Log)

---

## 10) Related links

- Approval Queue: `/docs/new/en/admin/risk-compliance/approval-queue.md`
- Fraud Check: `/docs/new/en/admin/risk-compliance/fraud-check.md`
- Responsible Gaming: `/docs/new/en/admin/risk-compliance/responsible-gaming.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
