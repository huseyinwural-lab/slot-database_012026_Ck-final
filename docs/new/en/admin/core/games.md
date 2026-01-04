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

## 4) Core workflows

### 4.1 Search/filter games (Slots & Games)
1) Open **Slots & Games** tab.
2) Use **Category filter** (e.g., Slot, Crash, Dice, Table Poker, Table Blackjack).
3) (If implemented in the build) use provider/supplier filters.

**API calls (observed from frontend):**
- List games: `GET /api/v1/games?category=<...>&page=<n>&page_size=<n>`

### 4.2 Enable/disable a game
1) In the **Slots & Games** list, toggle the game’s status.
2) Refresh the list to confirm updated status.

**API calls (observed from frontend):**
- Toggle: `POST /api/v1/games/{game_id}/toggle`

### 4.3 Live tables (create + validate)
1) Open **Live Tables** tab.
2) Use **Create Table** action.
3) Fill required fields (name/provider/min bet/max bet).
4) Save and confirm it appears in the table list.

**API calls (observed from frontend):**
- List tables: `GET /api/v1/tables`
- Create table: `POST /api/v1/tables`

### 4.4 Upload & Import (manual bundle)

The UI supports a “manual upload + preview + confirm import” flow.

Observed client flow:
1) Select **Upload & Import**.
2) Choose upload method (file-based).
3) Upload a bundle (JSON/ZIP) and optional metadata (source_label, notes, client_type, launch_url, min_version).
4) Review **preview items** and errors/warnings.
5) Click **Import** to finalize.

**API calls (observed from frontend):**
- Manual upload/analyze: `POST /api/v1/game-import/manual/upload` (multipart)
- Preview job details: `GET /api/v1/game-import/jobs/{job_id}`
- Confirm import: `POST /api/v1/game-import/jobs/{job_id}/import`

**Important implementation note:** in the current backend routes, `/api/v1/game-import` is a stub and the “manual/*” endpoints are not present. In this build, the UI may therefore receive **404 Not Found** for the manual import endpoints.

---

## 5) Field guide (practical tips)

- Always confirm **tenant context** before enabling/disabling games.
- Prefer making changes during low-traffic windows.
- After toggles/imports, expect propagation delays if there is caching on the lobby/client side.
- For VIP visibility rules, validate against the VIP Games configuration (do not assume “VIP” is implicit).

**Do not:**
- Enable a large batch without a rollback plan.
- Import a catalog bundle without validating required fields and uniqueness.

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum set for incident readiness (8+ items).

1) **Symptom:** A game is not visible in the list
   - Likely cause: category filter excludes it; wrong tenant context.
   - Fix: set Category filter to **All**; verify tenant context.
   - Verification: list reload shows the game; DevTools shows `GET /api/v1/games` success.

2) **Symptom:** Toggle succeeds in UI but the game still appears unchanged
   - Likely cause: UI list not refreshed; backend toggle failed silently.
   - Fix: refresh the page; check Network for `POST /api/v1/games/{id}/toggle` response.
   - Verification: the game status changes after refresh and subsequent `GET /api/v1/games`.

3) **Symptom:** Game is enabled but players still don’t see it
   - Likely cause: player-side caching; feature gating; tenant-to-lobby mapping.
   - Fix: clear client cache where applicable; verify feature flags; re-check tenant mapping.
   - Verification: player lobby list endpoint returns expected items (see player lobby APIs), and no “blocked” entries in logs.

4) **Symptom:** Launch results in black screen / provider error
   - Likely cause: provider credentials/config missing; upstream provider outage; launch URL mismatch.
   - Fix: validate provider configuration and API keys; check provider status.
   - Verification: backend logs show successful launch/session creation; no provider error responses.

5) **Symptom:** Live table does not appear after creation
   - Likely cause: `POST /api/v1/tables` failed validation.
   - Fix: check required fields; retry creation.
   - Verification: Network shows 200/201 and `GET /api/v1/tables` includes the new table.

6) **Symptom:** Upload & Import returns 404 Not Found
   - Likely cause: backend endpoint not implemented in this build (`/api/v1/game-import/manual/*`).
   - Fix: confirm backend routes for game import are deployed; if not, use supported import path or defer.
   - Verification: `POST /api/v1/game-import/manual/upload` returns 200 and job id.

7) **Symptom:** Import shows “validation failed”
   - Likely cause: missing required fields, invalid enum values, malformed bundle.
   - Fix: correct bundle format and required fields; re-upload.
   - Verification: preview job shows `total_errors=0` and items are listed.

8) **Symptom:** Import creates duplicates
   - Likely cause: missing uniqueness key / idempotency strategy; duplicate provider IDs.
   - Fix: enforce unique identifiers in the bundle; re-run with a corrected dataset.
   - Verification: after import, list shows a single canonical entry per unique id.

9) **Symptom:** VIP game becomes visible to normal players
   - Likely cause: incorrect segmentation/visibility mapping or VIP controls not applied.
   - Fix: validate VIP Games and segment targeting.
   - Verification: player-side test account outside VIP segment cannot see the game.

---

## 7) Resolution steps (step-by-step)

1) Capture evidence in DevTools:
   - failing request path
   - status code
   - response payload
2) Confirm tenant context.
3) Re-run the action once (toggle/import), then refresh.
4) If still failing, check backend logs for the same timeframe and the endpoint path.
5) If the issue impacts players, validate on the player lobby side.

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
- Typical expected actions (naming varies by implementation): `game.updated`, `game.imported`, `table.created`.

### 8.5 Database verification (if applicable)
- Tenant-scoped game records are stored in `game`-related tables/models.
- If you suspect wrong tenant scoping, verify `tenant_id` alignment for the affected game.

---

## 9) Security notes + rollback

- Catalog visibility changes can immediately impact revenue and player experience.
- Rollback approach (safe):
  1) Disable the impacted game(s).
  2) Revert mappings/segments.
  3) Re-test player visibility.

---

## 10) Related links

- VIP visibility: `/docs/new/en/admin/core/vip-games.md`
- Tenant context: `/docs/new/en/admin/system/tenants.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
