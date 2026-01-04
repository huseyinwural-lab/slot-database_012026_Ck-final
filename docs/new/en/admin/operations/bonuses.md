# Bonuses (EN)

**Menu path (UI):** Operations → Bonuses  
**Frontend route:** `/bonuses`  
**Feature flag (UI):** `can_manage_bonus`  

---

## Ops Checklist (read first)

- Bonuses are money-equivalent (promo balance). Treat changes as financial.
- Every create/toggle/grant must have:
  - **Reason** (UI requires it; backend enforces it)
  - evidence in **Audit Log**
  - anomaly monitoring in **Logs**
- Use Kill Switch to pause bonuses module during abuse waves.

---

## 1) Purpose and scope

Bonuses module manages:
- bonus campaigns (deposit match, free spins)
- status changes (activate/pause)
- manual bonus grants to players

Frontend: `frontend/src/pages/BonusManagement.jsx`.
Backend: `backend/app/routes/bonuses.py`.

---

## 2) Who uses this / permission requirements

- CRM/Retention Ops
- Fraud/Risk for abuse response

Access:
- UI gated by `can_manage_bonus`
- backend requires admin auth and tenant context
- backend enforces reason via `require_reason`

---

## 3) Core workflows

### 3.1 List campaigns
**API calls:**
- `GET /api/v1/bonuses/campaigns`

### 3.2 Create a campaign
1) Click **New Campaign**.
2) Fill:
   - name
   - type (deposit_match / free_spins)
   - config: multiplier, wagering_mult, min_deposit
   - reason (audit)
3) Create.

**API calls:**
- `POST /api/v1/bonuses/campaigns`

### 3.3 Pause/activate a campaign
1) Click Pause/Activate.
2) Provide reason.

**API calls:**
- `POST /api/v1/bonuses/campaigns/{id}/status`

> Note: backend currently expects `status` as embedded body; UI sends `{ status, reason }`.

### 3.4 Manual grant to a player
Used by backend but may not be exposed in current UI.

**API calls:**
- `POST /api/v1/bonuses/grant`

---

## 4) Operational notes

- Default wagering multipliers can create high churn if too strict.
- Monitor abuse signals:
  - repeated grant attempts
  - players repeatedly hitting 409 conflicts
  - sudden bonus-balance inflation

---

## 5) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Bonuses menu not visible.
   - **Likely cause:** `can_manage_bonus` capability missing.
   - **Fix:** grant feature.
   - **Verification:** menu appears.

2) **Symptom:** Create campaign fails with 400 REASON_REQUIRED.
   - **Likely cause:** reason missing.
   - **Fix:** provide `reason` in body or `X-Reason` header.
   - **Verification:** POST succeeds.

3) **Symptom:** Create campaign returns 422.
   - **Likely cause:** config values not numeric.
   - **Fix:** ensure multiplier/wagering/min_deposit are numbers.
   - **Verification:** campaign created.

4) **Symptom:** List campaigns returns empty unexpectedly.
   - **Likely cause:** tenant context mismatch.
   - **Fix:** confirm tenant impersonation header.
   - **Verification:** list shows campaigns.

5) **Symptom:** Status change fails with 422.
   - **Likely cause:** backend expects `status` embedded string, but UI sends object.
   - **Fix:** align backend to accept `{ status, reason }`.
   - **Verification:** status changes and persists.

6) **Symptom:** Status change fails with 400 REASON_REQUIRED.
   - **Likely cause:** reason not passed.
   - **Fix:** include reason in request.
   - **Verification:** audit event created.

7) **Symptom:** Grant fails with 409.
   - **Likely cause:** active grant already exists for player/campaign.
   - **Fix:** check player bonus history; avoid duplicate grants.
   - **Verification:** second grant is blocked as designed.

8) **Symptom:** Bonus balance increases but wagering requirement doesn’t.
   - **Likely cause:** player balance update logic not consistent.
   - **Fix:** verify player wallet updates.
   - **Verification:** `wagering_remaining` updated.

9) **Symptom:** No audit evidence for bonus changes.
   - **Likely cause:** audit integration missing.
   - **Fix:** ensure audit.log_event is called.
   - **Verification:** Audit Log contains `BONUS_*` actions.

---

## 6) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI status update body doesn’t match backend expectation.
   - **Likely Cause:** backend uses `status: str = Body(..., embed=True)`.
   - **Impact:** status toggle can fail (422).
   - **Admin Workaround:** none.
   - **Escalation Package:** capture 422 body for `/bonuses/campaigns/{id}/status`.
   - **Resolution Owner:** Backend
   - **Verification:** backend accepts `{ status, reason }`.

2) **Symptom:** UI doesn’t expose manual grant workflow.
   - **Likely Cause:** missing UI screen.
   - **Impact:** support/ops can’t grant bonuses safely.
   - **Resolution Owner:** Frontend/Product

---

## 7) Verification (UI + Logs + Audit + DB)

### 7.1 UI
- Campaign appears in table.
- Toggle changes status.

### 7.2 System → Logs
- Search for `/api/v1/bonuses/*` 4xx/5xx.

### 7.3 System → Audit Log
- Verify `BONUS_CAMPAIGN_CREATE`, `BONUS_CAMPAIGN_STATUS_CHANGE`, `BONUS_GRANT`.

### 7.4 DB verification
- `bonus_campaign` rows created.
- `bonus_grant` rows created for grants.

---

## 8) Security notes + rollback

- Rollback:
  - pause campaign
  - revoke bonus grants (requires implementation)

---

## 9) Related links

- Kill Switch: `/docs/new/en/admin/operations/kill-switch.md`
- Players: `/docs/new/en/admin/core/players.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
