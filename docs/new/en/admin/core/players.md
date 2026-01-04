# Players (EN)

**Menu path (UI):** Core → Players  
**Frontend route:** `/players`  
**Owner-only:** No  

---

## 1) Purpose and scope

The Players menu is the primary operational surface for searching, reviewing, and managing player accounts within the selected tenant. It supports investigations (risk/support), operational actions (status changes), and navigation into player-level details.

---

## 2) Who uses this / permission requirements

- Tenant Admin / Ops: day-to-day player management.
- Support: player case resolution (login issues, restrictions, disputes).
- Risk: investigating suspicious activity and applying restrictions.
- Platform Owner: cross-tenant visibility when tenant context is selected.

---

## 3) Sub-sections / screens

In the current UI:
- Player list (`frontend/src/pages/PlayerList.jsx`)
- Player detail (`frontend/src/pages/PlayerDetail.jsx`)

---

## 4) Core workflows (step-by-step)

### 4.1 Search and filter
1) Open Players.
2) Use the **Search** field (username/email).
3) Use **Status** filter (e.g., active/disabled/all).
4) (Optional) enable **Include disabled** if you need to see soft-disabled accounts.

**API calls (observed from frontend):**
- List: `GET /api/v1/players?search=<q>&status=<status>&page=<n>&page_size=<n>`

### 4.2 Open a player profile
1) From the list, click a player row.
2) Review profile fields and activity.

**API calls:**
- Detail: `GET /api/v1/players/{player_id}`

### 4.3 Update a player (profile/status)
1) Open Player detail.
2) Apply the change (status, notes, restrictions depending on UI).

**API calls (backend supported):**
- Update: `PUT /api/v1/players/{player_id}`

### 4.4 Disable a player (soft delete)
1) Open Player detail.
2) Select the disable action.
3) Confirm.

**API calls (backend supported):**
- Disable: `DELETE /api/v1/players/{player_id}` (soft disable)

---

## 5) Field guide (practical tips)

- Always validate tenant context before applying restrictions.
- Prefer **soft disable** for containment; avoid destructive actions.
- For wallet disputes, cross-check with Finance ledger menus.

**Do not:**
- Disable a player without recording a reason in Support notes / audit trail.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

> Minimum set (9 items).

1) **Symptom:** Player cannot be found.
   - **Likely cause:** Search term mismatch; wrong tenant context.
   - **Fix:** Search by email and username; verify tenant context.
   - **Verification:** `GET /api/v1/players` returns expected results.

2) **Symptom:** Player list is empty.
   - **Likely cause:** Filters too restrictive; selected status hides disabled players.
   - **Fix:** Set status to `all`; enable include_disabled if needed.
   - **Verification:** List endpoint returns items and meta.

3) **Symptom:** Clicking a player returns 404.
   - **Likely cause:** Wrong tenant boundary (player belongs to another tenant).
   - **Fix:** Verify tenant context; search the player in the correct tenant.
   - **Verification:** `GET /api/v1/players/{id}` returns 200 in the correct tenant.

4) **Symptom:** Update fails with 400.
   - **Likely cause:** Invalid field name or invalid status value.
   - **Fix:** Only update supported fields; retry with valid values.
   - **Verification:** `PUT /api/v1/players/{id}` returns success.

5) **Symptom:** Disable fails with 403.
   - **Likely cause:** Role missing permission.
   - **Fix:** Use an admin with appropriate role; escalate if permissions are misconfigured.
   - **Verification:** Disable action succeeds and player status becomes `disabled`.

6) **Symptom:** Disabled player still appears as active.
   - **Likely cause:** UI cache not refreshed.
   - **Fix:** Refresh page; re-fetch list.
   - **Verification:** `GET /api/v1/players` shows `status=disabled`.

7) **Symptom:** Player cannot log in after changes.
   - **Likely cause:** Player status disabled; additional restrictions applied.
   - **Fix:** Verify player status and restrictions; revert if unintended.
   - **Verification:** Login attempts succeed and no auth errors in logs.

8) **Symptom:** Player segmentation/labels missing.
   - **Likely cause:** Feature not enabled or data not loaded.
   - **Fix:** Confirm feature entitlements; refresh; escalate if segment service is down.
   - **Verification:** UI shows segments; no errors in logs.

9) **Symptom:** Slow player search.
   - **Likely cause:** Large dataset or inefficient search.
   - **Fix:** Use more specific query; reduce page size.
   - **Verification:** Response time decreases.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI actions fail with 404/501 on advanced player operations (risk flags, wallet tools).
   - **Likely cause:** UI expects additional endpoints that are not present in this backend build.
   - **Impact:** Specific player-side operations are blocked; basic list/detail/update/disable may still work.
   - **Admin Workaround:** No admin-side workaround if the action requires a missing endpoint.
   - **Escalation Package:**
     - Method + path: (capture from DevTools → Network)
     - Request sample: export as cURL from DevTools
     - Expected vs actual: expected 200/204, actual 404
     - Logs: search backend logs for `player` + the missing path
   - **Resolution Owner:** Backend
   - **Verification:** Missing endpoint returns 200 and UI action succeeds.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Search returns results.
- Player detail loads.
- Status updates persist after refresh.

### 8.2 System → Logs
- Look for errors on player endpoints.

### 8.3 App / container logs
- Search keywords:
  - `players`
  - `Player not found`
  - `tenant_id`

### 8.4 System → Audit Log
- Expected events (if enabled): `player.create`, `player.update`, `player.disabled`.

### 8.5 DB audit (if available)
- `player` table: status changes and tenant_id.
- `auditevent` table: actor + action + target_id.

---

## 9) Security notes + rollback

- Player disable is a high-impact control. Always record reason.
- Rollback: re-enable player by updating status back to active (if supported) and validate login.

---

## 10) Related links

- Finance: `/docs/new/en/admin/core/finance.md`
- Withdrawals: `/docs/new/en/admin/core/withdrawals.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
