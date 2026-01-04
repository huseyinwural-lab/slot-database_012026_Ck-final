# Games (EN)

**Menu path (UI):** Core → Games  
**Frontend route:** `/games`  
**Owner-only:** No  

---

## 1) Purpose and scope

The Games menu is the operational control plane for the tenant’s game catalog: browsing available games, enabling/disabling visibility, managing live tables, and handling catalog ingestion/import flows.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin): can operate across tenants by selecting the intended tenant context.
- Tenant Admin / Ops: day-to-day catalog operations (enable/disable, validate visibility).
- Risk/Compliance: may validate visibility/segments during incidents.

---

## 3) Sub-sections (tabs)

In the current UI (`frontend/src/pages/GameManagement.jsx`):
- **Slots & Games**
- **Live Tables**
- **Upload & Import**

---

## 4) Core workflows (step-by-step)

### 4.1 Search/filter games (Slots & Games)
1) Open **Slots & Games** tab.
2) Use **Category filter** (e.g., Slot, Crash, Dice, Table Poker, Table Blackjack).
3) (If implemented) use provider/supplier filters.

**API calls (observed from frontend):**
- List games: `GET /api/v1/games?category=<...>&page=<n>&page_size=<n>`

### 4.2 Enable/disable a game
1) In the **Slots & Games** list, toggle the game’s status.
2) Refresh the list to confirm updated status.

**API calls (observed from frontend):**
- Toggle: `POST /api/v1/games/{game_id}/toggle`

### 4.3 Live tables (create + validate)
1) Open **Live Tables** tab.
2) Select **Create Table**.
3) Fill required fields (name/provider/min bet/max bet).
4) Save and confirm it appears.

**API calls (observed from frontend):**
- List tables: `GET /api/v1/tables`
- Create table: `POST /api/v1/tables`

### 4.4 Upload & Import (manual bundle)

The UI supports a “manual upload + preview + confirm import” flow.

1) Select **Upload & Import**.
2) Choose the file-based method.
3) Upload a bundle (JSON/ZIP) and optional metadata (source_label, notes, client_type, launch_url, min_version).
4) Review preview items and errors/warnings.
5) Click **Import** to finalize.

**API calls (observed from frontend):**
- Manual upload/analyze: `POST /api/v1/game-import/manual/upload` (multipart)
- Preview job details: `GET /api/v1/game-import/jobs/{job_id}`
- Confirm import: `POST /api/v1/game-import/jobs/{job_id}/import`

**Important implementation note:** In the current backend routes, `/api/v1/game-import` is a stub and the “manual/*” endpoints are not present. In this build, the UI may receive **404 Not Found** for these endpoints.

---

## 5) Field guide (practical tips)

- Always confirm **tenant context** before enable/disable.
- Prefer changes during low-traffic windows.
- After toggles/imports, expect propagation delays if the lobby/client has caching.
- For VIP visibility, validate against VIP configuration (do not assume “VIP” is implicit).

**Do not:**
- Enable a large batch without a rollback plan.
- Import a catalog bundle without validating required fields and uniqueness.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

> Minimum set for incident readiness (8+).

1) **Symptom:** A game is not visible in the list.
   - **Likely cause:** Category filter excludes it; wrong tenant context.
   - **Fix:** Set Category filter to **All**; verify tenant context.
   - **Verification:** List reload shows the game; `GET /api/v1/games` returns 200.

2) **Symptom:** Toggle appears to work, but the list shows the old status.
   - **Likely cause:** UI did not refresh; toggle request failed.
   - **Fix:** Refresh; check `POST /api/v1/games/{id}/toggle` response.
   - **Verification:** After refresh, the game status changes and `GET /api/v1/games` reflects it.

3) **Symptom:** Game is enabled but players still don’t see it.
   - **Likely cause:** Player-side caching; feature gating; tenant-to-lobby mapping.
   - **Fix:** Clear client cache where applicable; validate feature flags; confirm correct tenant mapping.
   - **Verification:** Player lobby list endpoint includes the game; no “blocked” errors in logs.

4) **Symptom:** Launch results in a black screen / provider error.
   - **Likely cause:** Provider credentials/config missing; upstream provider outage; launch URL mismatch.
   - **Fix:** Validate provider configuration and API keys; check provider status.
   - **Verification:** Backend logs show a successful launch/session; provider responses are not errors.

5) **Symptom:** Live table does not appear after creation.
   - **Likely cause:** Validation error on `POST /api/v1/tables`.
   - **Fix:** Verify required fields and numeric ranges; retry.
   - **Verification:** `GET /api/v1/tables` includes the new row.

6) **Symptom:** Upload & Import returns 404 Not Found.
   - **Likely cause:** Backend endpoints not implemented (`/api/v1/game-import/manual/*`).
   - **Fix:** Confirm backend release includes these routes; otherwise use supported import path or defer.
   - **Verification:** `POST /api/v1/game-import/manual/upload` returns 200 + job id.

7) **Symptom:** Import shows “validation failed”.
   - **Likely cause:** Missing required fields; invalid enums; malformed bundle.
   - **Fix:** Correct the bundle format/fields; re-upload.
   - **Verification:** Preview shows `total_errors=0` and items list is populated.

8) **Symptom:** Import created duplicate entries.
   - **Likely cause:** Missing uniqueness key / idempotency strategy; duplicate provider IDs.
   - **Fix:** Ensure unique identifiers; re-run with corrected dataset.
   - **Verification:** Post-import, only one entry exists per unique id.

9) **Symptom:** VIP game is visible to non-VIP users.
   - **Likely cause:** Segment/visibility misconfiguration.
   - **Fix:** Validate VIP rules and segment targeting; revert misapplied mappings.
   - **Verification:** Non-VIP test account cannot see the VIP game.

---

## 7) Resolution steps (step-by-step)

1) Capture evidence in DevTools (Network): failing request path + status + payload.
2) Confirm tenant context.
3) Re-run the action once, then refresh.
4) Check backend logs for the same timeframe and endpoint path.
5) Validate player-side visibility if impacted.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Games list reflects correct enabled/disabled state.
- Live Tables list contains the created tables.
- Upload & Import shows preview status and items.

### 8.2 System → Logs
- Check runtime errors/timeouts around game toggle/import.

### 8.3 App / container logs
- Search keywords:
  - `games` / `toggle`
  - `tables`
  - `game-import` / `import`
  - provider name / provider error codes

### 8.4 System → Audit Log
- If audit events exist for catalog operations, filter by timeframe and resource id.
- Typical actions (naming varies): `game.updated`, `game.imported`, `table.created`, `visibility.changed`.

### 8.5 DB audit (if present)
- Tenant-scoped game records should match the intended `tenant_id`.
- If wrong-tenant exposure is suspected, verify `tenant_id` alignment for the affected game.

---

## 9) Security notes + rollback

- Catalog visibility changes can immediately impact revenue and player experience.

Rollback (recommended):
1) Disable impacted games.
2) Revert mappings/segments.
3) Re-test player visibility.

---

## 10) Related links

- VIP visibility: `/docs/new/en/admin/core/vip-games.md`
- Tenant context safety: `/docs/new/en/admin/system/tenants.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
