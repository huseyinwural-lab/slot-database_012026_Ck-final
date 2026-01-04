# Affiliates (EN)

**Menu path (UI):** Operations → Affiliates  
**Frontend route:** `/affiliates`  
**Feature flag (UI):** `can_manage_affiliates`  

---

## Ops Checklist (read first)

- Confirm module is enabled (Kill Switch: `affiliates`).
- For new partners/offers/links/payouts:
  - collect evidence (request/response)
  - store decision record (why approved)
- Monitor abuse risk (self-referrals, bonus abuse via affiliate traffic).

---

## 1) Purpose and scope

Affiliates manages acquisition partners:
- partners (affiliates)
- offers
- tracking links
- payouts
- creatives

Frontend: `frontend/src/pages/AffiliateManagement.jsx`.
Backend: `backend/app/routes/affiliates.py`.

---

## 2) Who uses this / permission requirements

- Growth/Marketing Ops
- Finance (payouts)

Access:
- UI requires `can_manage_affiliates`
- backend enforces module access via `enforce_module_access(..., module_key="affiliates")`

---

## 3) Sub-sections / tabs (UI)

AffiliateManagement tabs:
- Partners
- Offers
- Tracking
- Payouts
- Creatives
- Reports

---

## 4) Core workflows

### 4.1 Partners list + create
**API calls (UI):**
- `GET /api/v1/affiliates`
- `POST /api/v1/affiliates`

### 4.2 Offers
**API calls (UI):**
- `GET /api/v1/affiliates/offers`
- `POST /api/v1/affiliates/offers`

### 4.3 Tracking links
**API calls (UI):**
- `GET /api/v1/affiliates/links`
- `POST /api/v1/affiliates/links`

### 4.4 Payouts
**API calls (UI):**
- `GET /api/v1/affiliates/payouts`
- `POST /api/v1/affiliates/payouts`

### 4.5 Creatives
**API calls (UI):**
- `GET /api/v1/affiliates/creatives`
- `POST /api/v1/affiliates/creatives`

---

## 5) Operational notes

- Partner approval should include:
  - identity verification (business)
  - traffic source review
  - payout terms
- Use unique tracking links per channel.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Affiliates menu not visible.
   - **Likely cause:** `can_manage_affiliates` missing.
   - **Fix:** grant feature.
   - **Verification:** menu appears.

2) **Symptom:** Affiliates endpoints return 503.
   - **Likely cause:** Kill Switch disabled module.
   - **Fix:** re-enable `affiliates`.
   - **Verification:** endpoints return 200.

3) **Symptom:** Offers/Payouts/Creatives tabs always empty.
   - **Likely cause:** backend stubs return `[]`.
   - **Fix:** implement persistence.
   - **Verification:** created items show.

4) **Symptom:** Create partner fails with 422.
   - **Likely cause:** payload missing required fields.
   - **Fix:** validate form fields.
   - **Verification:** partner created.

5) **Symptom:** Create offer fails with 404.
   - **Likely cause:** backend route missing.
   - **Fix:** implement `/affiliates/offers`.
   - **Verification:** offer created.

6) **Symptom:** Tracking links fail to generate.
   - **Likely cause:** backend expects different schema.
   - **Fix:** align `newLink` contract.
   - **Verification:** link appears and URL is copyable.

7) **Symptom:** Payout record created but finance cannot reconcile.
   - **Likely cause:** payout lacks period metadata.
   - **Fix:** add period_start/period_end and ledger references.
   - **Verification:** payout is traceable.

8) **Symptom:** No audit trail for affiliate changes.
   - **Likely cause:** affiliate routes not audited.
   - **Fix:** add audit events for create/approve/payout.
   - **Verification:** Audit Log entries exist.

9) **Symptom:** Self-referral abuse detected.
   - **Likely cause:** no anti-fraud checks.
   - **Fix:** integrate with Risk Rules; add KYC for affiliates.
   - **Verification:** suspicious traffic blocked.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI calls endpoints that are not implemented.
   - **Likely Cause:** `backend/app/routes/affiliates.py` implements only base affiliate CRUD + several stubs.
   - **Impact:** Offers/Payouts/Creatives remain non-functional.
   - **Admin Workaround:** track offers/payouts externally.
   - **Escalation Package:** implement data models + endpoints.
   - **Resolution Owner:** Backend

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Partner created; appears in list.

### 8.2 System → Logs
- Check `/api/v1/affiliates*` errors.

### 8.3 System → Audit Log
- Verify affiliate create/approve/payout events (if implemented).

### 8.4 DB verification
- `affiliate` rows exist per tenant.

---

## 9) Security notes

- Validate affiliate traffic sources.
- Ensure GDPR/consent requirements.

---

## 10) Related links

- Kill Switch: `/docs/new/en/admin/operations/kill-switch.md`
- Risk Rules: `/docs/new/en/admin/risk-compliance/risk-rules.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
