# Robots (EN)

**Menu path (UI):** Game Engine → Robots  
**Frontend route:** `/robots`  
**Feature flag (UI):** `can_use_game_robot`  

---

## Ops Checklist (read first)

- Use Robots to manage the **math engine definition** for games.
- Risky operations:
  - toggling robots (may affect availability/behavior)
  - cloning robots (spawns new config versions)
- Always provide a **reason** for write operations (backend enforces it).
- Validate changes in:
  - UI (status change)
  - **Audit Log** (`ROBOT_TOGGLE`, `ROBOT_CLONE`)
  - **Logs** (4xx/5xx on robots endpoints)

---

## 1) Purpose and scope

Robots is the registry of **Game Math Engines**.
A RobotDefinition typically references math assets (reel sets, paytables) via `config` fields such as:
- `reel_set_ref`
- `paytable_ref`

Frontend: `frontend/src/pages/RobotsPage.jsx`.
Backend: `backend/app/routes/robots.py`.

---

## 2) Who uses this / permission requirements

- Game Ops / Game Engine team
- Platform Owner (depending on governance)

Access:
- UI gated by `can_use_game_robot`.
- Backend requires admin auth.

---

## 3) What you can do (UI)

- Search robots
- View robot config JSON
- Toggle active/inactive
- Clone robot

> Note: UI does not currently show a create-from-scratch flow; cloning is the main versioning mechanism.

---

## 4) Core workflows

### 4.1 List/search robots
1) Open Game Engine → Robots.
2) Use search input.

**API calls (UI):**
- `GET /api/v1/robots?search=<text>`

Expected response shape:
- `{ items: RobotDefinition[], meta: { total, page, page_size } }`

### 4.2 View robot config
1) Click the Eye icon.
2) Review JSON.

**Data source:** robot object `config`.

### 4.3 Toggle robot active status
1) Use the switch control.
2) Provide a reason when prompted (backend requires it).

**API calls:**
- `POST /api/v1/robots/{robot_id}/toggle`

**Audit events (expected):**
- `ROBOT_TOGGLE`

### 4.4 Clone a robot
1) Click Clone.
2) Provide a reason.

**API calls:**
- `POST /api/v1/robots/{robot_id}/clone`

**Audit events (expected):**
- `ROBOT_CLONE`

---

## 5) Field guide (practical tips)

- Keep Robot configs immutable by convention; clone for changes.
- Use a consistent naming scheme:
  - `game_x_v1`, `game_x_v2`.
- Ensure referenced Math Assets exist before enabling a robot.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Robots page shows empty list.
   - **Likely cause:** no robots exist yet, or tenant context mismatch.
   - **Fix:** seed robots; confirm tenant context.
   - **Verification:** GET returns items.

2) **Symptom:** Robots list fails with 401.
   - **Likely cause:** session expired.
   - **Fix:** re-login.
   - **Verification:** GET 200.

3) **Symptom:** Robots list fails with 403.
   - **Likely cause:** missing `can_use_game_robot` capability.
   - **Fix:** grant feature.
   - **Verification:** route accessible.

4) **Symptom:** Toggle fails with 400 REASON_REQUIRED.
   - **Likely cause:** reason not provided.
   - **Fix:** send `X-Reason` header or reason field as required by client.
   - **Verification:** toggle returns 200.

5) **Symptom:** Toggle returns 404.
   - **Likely cause:** robot_id not found.
   - **Fix:** refresh list; retry.
   - **Verification:** robot exists.

6) **Symptom:** Clone fails with 400 REASON_REQUIRED.
   - **Likely cause:** missing reason.
   - **Fix:** provide reason.
   - **Verification:** clone returns 200.

7) **Symptom:** Clone fails with 422.
   - **Likely cause:** backend expects embedded `name_suffix`.
   - **Fix:** keep default; if overriding, send body `{ "name_suffix": " (Cloned)" }`.
   - **Verification:** new robot appears.

8) **Symptom:** Audit Log does not show robot changes.
   - **Likely cause:** audit events not persisted or not visible.
   - **Fix:** confirm Audit Log backend route and filters.
   - **Verification:** `ROBOT_TOGGLE`/`ROBOT_CLONE` visible.

9) **Symptom:** Robot enabled but game behavior doesn’t change.
   - **Likely cause:** robot binding to game is separate (GameRobotBinding).
   - **Fix:** verify game binding endpoints/workflow.
   - **Verification:** the game references the intended robot_id.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI does not prompt for a reason but backend requires it.
   - **Likely Cause:** `toggle_robot` and `clone_robot` depend on `require_reason`.
   - **Impact:** toggles/clones can fail with REASON_REQUIRED.
   - **Admin Workaround:** none (needs UI support).
   - **Escalation Package:** capture 400 body for toggle/clone.
   - **Resolution Owner:** Frontend/Backend

2) **Symptom:** No explicit create robot flow exists.
   - **Likely Cause:** product choice to use cloning.
   - **Impact:** cannot create a robot without an existing template.
   - **Resolution Owner:** Product

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Toggle changes badge (Active/Inactive).
- Clone adds a new row.

### 8.2 System → Logs
- Search `/api/v1/robots` 4xx/5xx.

### 8.3 System → Audit Log
- Filter by `ROBOT_TOGGLE`, `ROBOT_CLONE`.

### 8.4 DB verification
- `robotdefinition` rows exist.

---

## 9) Security notes + rollback

- Enabling robots can change game outcomes.
- Rollback:
  - toggle robot back to previous state
  - or revert binding to prior robot version

---

## 10) Related links

- Math Assets: `/docs/new/en/admin/game-engine/math-assets.md`
- Simulator: `/docs/new/en/admin/system/simulator.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
