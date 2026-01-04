# Fraud Check (EN)

**Menu path (UI):** Risk & Compliance → Fraud Check  
**Frontend route:** `/fraud`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Treat Fraud Check results as **decision support**, not a final adjudication.
- Capture evidence:
  - request payload + response (DevTools → Network)
  - runtime errors in **Logs**
  - any follow-up action evidence in **Audit Log** (if implemented)
- Do not paste secrets or full PII into prompts.

---

## 1) Purpose and scope

Fraud Check allows an admin to submit a transaction-like payload and receive a risk assessment.

In this build, UI is implemented in `frontend/src/pages/FraudCheck.jsx` and mentions “via OpenAI”.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin)
- Risk / Fraud team (if roles exist)

---

## 3) Core workflow

### 3.1 Run an analysis
1) Open Fraud Check.
2) Fill inputs:
   - amount
   - merchant
   - customer email
   - IP address
3) Click **Check Risk Score**.

**API calls (as used by UI):**
- `POST /api/v1/fraud/analyze`

Expected response fields (as rendered by UI):
- `fraud_risk_score` (0.0–1.0)
- `is_fraudulent` (bool)
- `recommendations` (string)
- `risk_factors` (array of strings)
- `confidence_level` (0.0–1.0)

---

## 4) Field guide (practical tips)

- Use realistic but **non-sensitive** test data.
- Prefer scenario-based evaluation:
  - high amount + suspicious email domain
  - high-risk IP ranges
- Treat the model output as a signal to trigger a case / review workflow.

---

## 5) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Analyze returns 404.
   - **Likely cause:** `/api/v1/fraud/analyze` is not implemented.
   - **Fix:** implement backend route; or disable the feature.
   - **Verification:** POST returns 200 with expected schema.

2) **Symptom:** Analyze returns 500.
   - **Likely cause:** model/integration failure.
   - **Fix:** check integration keys/config; inspect Logs.
   - **Verification:** POST returns stable response.

3) **Symptom:** Analyze returns 422.
   - **Likely cause:** request body contract mismatch.
   - **Fix:** align payload shape to backend schema.
   - **Verification:** request accepted.

4) **Symptom:** Analyze works but UI crashes when rendering.
   - **Likely cause:** response missing fields (`risk_factors` not an array, etc.).
   - **Fix:** normalize backend response.
   - **Verification:** UI renders result card.

5) **Symptom:** Risk score always 0% or 100%.
   - **Likely cause:** stubbed backend or hardcoded model response.
   - **Fix:** verify backend logic; add test cases.
   - **Verification:** score varies by input.

6) **Symptom:** 401 on analyze.
   - **Likely cause:** session expired.
   - **Fix:** re-login.
   - **Verification:** POST 200.

7) **Symptom:** 403 on analyze.
   - **Likely cause:** role not allowed.
   - **Fix:** use owner admin; implement entitlements.
   - **Verification:** role access works as designed.

8) **Symptom:** PII/security concerns raised.
   - **Likely cause:** prompts include sensitive data.
   - **Fix:** redact; restrict access; log only hashed identifiers.
   - **Verification:** Logs/Audit avoid sensitive payloads.

9) **Symptom:** No audit evidence for model-triggered decisions.
   - **Likely cause:** analysis isn’t audited.
   - **Fix:** add `fraud.analysis.run` event to Audit Log.
   - **Verification:** Audit Log shows analysis entries.

---

## 6) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI calls `POST /api/v1/fraud/analyze` but backend exposes only `GET /api/v1/fraud/`.
   - **Likely Cause:** `backend/app/routes/fraud_detection.py` is a stub.
   - **Impact:** Fraud Check UI cannot function.
   - **Admin Workaround:** None.
   - **Escalation Package:**
     - Method + path: `POST /api/v1/fraud/analyze`
     - Expected vs actual: expected analysis schema; actual 404
     - Keywords: `fraud/analyze`
   - **Resolution Owner:** Backend
   - **Verification:** POST exists and returns expected fields.

2) **Symptom:** UI text says “via OpenAI” but integration is not documented/visible.
   - **Likely Cause:** missing integration wiring.
   - **Impact:** operators cannot predict cost/latency or failure modes.
   - **Admin Workaround:** treat as unavailable until implemented.
   - **Escalation Package:** link fraud service implementation + model choice.
   - **Resolution Owner:** Backend/Platform
   - **Verification:** docs + runtime integration exist.

---

## 7) Verification (UI + Logs + Audit)

### 7.1 UI
- Result card renders and fields display.

### 7.2 System → Logs
- Search for `/api/v1/fraud/analyze` 4xx/5xx.

### 7.3 System → Audit Log
- If implemented, verify `fraud.analysis.run` events.

---

## 8) Security notes

- Treat inputs as sensitive; restrict who can run the tool.
- Log only minimal context; avoid raw emails/IPs in Logs/Audit.

---

## 9) Related links

- Risk Rules: `/docs/new/en/admin/risk-compliance/risk-rules.md`
- Approval Queue: `/docs/new/en/admin/risk-compliance/approval-queue.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
