# Responsible Gaming (EN)

**Menu path (UI):** Risk & Compliance → Responsible Gaming  
**Frontend route:** `/rg`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- RG actions are user-protective but legally sensitive.
- Always collect evidence:
  - request path + response (DevTools → Network)
  - **Audit Log** event for the action (if implemented)
  - runtime errors in **Logs**
- Never lift exclusions without an approval process.

---

## 1) Purpose and scope

Responsible Gaming (RG) enforces player protection controls:
- deposit/loss/session limits
- temporary cool-off
- self-exclusion (temporary/permanent)
- controlled admin overrides (high risk)

In this build, UI is implemented in `frontend/src/pages/ResponsibleGaming.jsx`.

---

## 2) Who uses this / permission requirements

- Platform Owner / Compliance
- Support (read-only) if allowed

---

## 3) Core workflow (as implemented in UI)

### 3.1 Find a player
1) Enter a player email.
2) Click Search.

> Note: UI contains explicit comments that this lookup may be mocked / not implemented.

### 3.2 Apply an RG action
1) Select action:
   - cooloff
   - exclude_temp / exclude_perm
   - lift (dangerous)
2) Provide a reason.
3) Click Apply Action.

**API calls (as used by UI):**
- `POST /api/v1/rg/admin/override/{player_id}`

---

## 4) Operational notes

- RG should be a closed-loop process:
  - action → audit evidence → player-facing verification
- If your jurisdiction requires approvals, route “lift” through Approval Queue.

---

## 5) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Player search always returns a demo profile.
   - **Likely cause:** UI is mocked.
   - **Fix:** implement lookup endpoint (e.g., admin player search by email).
   - **Verification:** real player profile loads.

2) **Symptom:** Apply Action returns 404.
   - **Likely cause:** `/api/v1/rg/admin/override/{player_id}` not implemented or route mismatch.
   - **Fix:** implement/admin-wire correct RG override route.
   - **Verification:** POST returns 200.

3) **Symptom:** Apply Action returns 422.
   - **Likely cause:** backend expects different payload fields (e.g., `lift_exclusion` vs `action`).
   - **Fix:** align UI payload with backend schema.
   - **Verification:** request accepted.

4) **Symptom:** Apply Action returns 400 “Reason required”.
   - **Likely cause:** backend enforces reason.
   - **Fix:** ensure reason is passed and non-empty.
   - **Verification:** action succeeds.

5) **Symptom:** Lift exclusion succeeds but player remains excluded.
   - **Likely cause:** player status not updated or cache.
   - **Fix:** ensure player status changes to active; verify in Logs.
   - **Verification:** player can log in and is not blocked.

6) **Symptom:** Self-exclusion endpoints behave inconsistently.
   - **Likely cause:** duplicate RG routes (`rg.py` vs `rg_player.py`) with different semantics.
   - **Fix:** consolidate routes; standardize on timezone-aware datetime.
   - **Verification:** consistent response contracts.

7) **Symptom:** 401/403 on RG endpoints.
   - **Likely cause:** auth/permissions.
   - **Fix:** re-login; use owner role.
   - **Verification:** endpoints return 200.

8) **Symptom:** No audit trail exists for RG actions.
   - **Likely cause:** only some RG actions are audited.
   - **Fix:** ensure all admin RG overrides write to Audit Log.
   - **Verification:** Audit Log shows `RG_ADMIN_OVERRIDE`.

9) **Symptom:** Jurisdiction requires approval but lift is done unilaterally.
   - **Likely cause:** Approval workflow not enforced.
   - **Fix:** integrate with Approval Queue or lock down lift.
   - **Verification:** lift requires an approval record.

---

## 6) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI sends `action` + `reason` but backend override expects different payload.
   - **Likely Cause:** `backend/app/routes/rg.py` uses `require_reason` and expects payload like `{ lift_exclusion: true }`.
   - **Impact:** UI cannot reliably apply RG actions.
   - **Admin Workaround:** none.
   - **Escalation Package:** capture 422 body; align payload and action mapping.
   - **Resolution Owner:** Backend/Frontend

2) **Symptom:** Player lookup by email is mocked.
   - **Likely Cause:** missing admin player search endpoint.
   - **Impact:** RG actions cannot be safely targeted.
   - **Resolution Owner:** Backend

---

## 7) Verification (UI + Logs + Audit + DB)

### 7.1 UI
- Action shows success toast.

### 7.2 System → Logs
- Check errors for `/api/v1/rg/*`.

### 7.3 System → Audit Log
- Verify `RG_ADMIN_OVERRIDE` exists (if auditing implemented).

### 7.4 DB verification
- `player_rg_profile` rows updated.

---

## 8) Security notes + rollback

- Lifting exclusions is high risk.
- Rollback:
  - re-apply exclusion
  - open an approval request (if policy requires)

---

## 9) Related links

- Approval Queue: `/docs/new/en/admin/risk-compliance/approval-queue.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
