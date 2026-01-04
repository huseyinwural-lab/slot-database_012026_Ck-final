# VIP Games (EN)

**Menu path (UI):** Core → VIP Games  
**Frontend route:** `/vip-games`  
**Owner-only:** No  

---

## Ops Checklist (read first)

- Confirm **tenant context** and confirm you are editing the correct tenant catalog.
- If incident: decide which direction you need:
  - “VIP game visible to normal players” → remove VIP visibility / rollback mapping.
  - “VIP user can’t see VIP game” → confirm VIP marker and propagation.
- Verify changes in **UI (VIP Games + Games)** and in **System → Audit Log**.
- If visibility changes don’t propagate: check **System → Logs** and container logs for `games` / `vip` / `tags`.

---

## 1) Purpose and scope

VIP Games controls which games are labeled as VIP-only (or VIP-highlighted) for high-value players. In this build, VIP membership is represented as a **game tag** (`VIP`) applied to the game record.

---

## 2) Who uses this / permission requirements

- Tenant Admin / Ops: can manage VIP catalog.
- Platform Owner: can operate across tenants when tenant context is selected.

---

## 3) VIP visibility criteria (how VIP is determined)

In the current implementation (`frontend/src/pages/VipGames.jsx`):
- A game is treated as VIP when `game.tags` contains `VIP`.

Important operational note:
- VIP tagging here is **catalog-side visibility metadata**, not a player segmentation engine.
- If your business rules require segment-based enforcement (VIP tier / cohorts), that must be enforced in player-facing lobby logic (feature flags/segments) in addition to the tag.

---

## 4) Core workflows (step-by-step)

### 4.1 View VIP games
1) Open VIP Games.
2) The page loads all games and filters those with `tags.includes('VIP')`.

**API calls (observed from frontend):**
- List games: `GET /api/v1/games` (UI expects array or paginated; it handles both)

### 4.2 Add a game to VIP
1) Click **Add VIP Game**.
2) Search for a game.
3) Click **Add**.

**API calls (observed from frontend):**
- Update tags: `PUT /api/v1/games/{game_id}/details` body `{ tags: [ ... , "VIP" ] }`

### 4.3 Remove a game from VIP
1) In VIP list, click remove (trash icon).

**API calls:**
- Update tags: `PUT /api/v1/games/{game_id}/details` body `{ tags: <tags without VIP> }`

### 4.4 Propagation / caching note
- Expect propagation delay if the player lobby caches catalog results.
- Always validate on a test player account after changes.

---

## 5) Field guide (practical tips)

- Always treat VIP visibility changes as revenue-impacting.
- Prefer changing one game at a time during incidents.
- Keep an incident note: what was changed, why, and rollback plan.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** VIP game is visible to normal users.
   - **Likely cause:** VIP tag applied but player-side enforcement/segment gating missing.
   - **Fix:** remove the `VIP` tag (temporary containment) and validate lobby rules.
   - **Verification:** non-VIP test account cannot see the game.

2) **Symptom:** VIP user cannot see a VIP game.
   - **Likely cause:** VIP tag not applied; caching delay; wrong tenant context.
   - **Fix:** verify the game has `VIP` tag; refresh caches / wait propagation; confirm tenant context.
   - **Verification:** VIP user sees the game after refresh/propagation.

3) **Symptom:** “Failed to update status” toast when adding/removing VIP.
   - **Likely cause:** missing backend endpoint or validation error.
   - **Fix:** check DevTools for failing request and payload; retry once.
   - **Verification:** `PUT /api/v1/games/{id}/details` returns 200.

4) **Symptom:** VIP Games list is empty but VIP is expected.
   - **Likely cause:** `GET /api/v1/games` returned empty; wrong tenant; API failure.
   - **Fix:** check Games page; verify tenant; check Network.
   - **Verification:** games list loads and VIP filter returns items.

5) **Symptom:** Game appears twice or VIP filter inconsistent.
   - **Likely cause:** duplicate catalog entries or inconsistent IDs.
   - **Fix:** locate duplicates in Games; disable duplicates.
   - **Verification:** single canonical entry remains.

6) **Symptom:** VIP tag removed but normal users still see the game.
   - **Likely cause:** lobby cache not refreshed.
   - **Fix:** invalidate cache (if supported) or wait TTL; re-test.
   - **Verification:** after TTL/refresh, the game disappears for normal users.

7) **Symptom:** VIP tag applied but VIP user still doesn’t see it.
   - **Likely cause:** player account not in VIP cohort/tier; lobby gating rules differ.
   - **Fix:** confirm player VIP status; confirm enforcement logic.
   - **Verification:** correct VIP player account sees the game.

8) **Symptom:** 404 Not Found on VIP update request.
   - **Likely cause:** backend does not expose `PUT /api/v1/games/{id}/details`.
   - **Fix:** no admin-side workaround.
   - **Verification:** endpoint exists and returns 200 after backend fix.

9) **Symptom:** “VIP” tag changes revert unexpectedly.
   - **Likely cause:** another system overwriting tags (import sync / provider sync).
   - **Fix:** pause sync job if applicable; coordinate with engineering.
   - **Verification:** tag remains stable across refreshes.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Add/Remove VIP fails with 404.
   - **Likely Cause:** UI calls `PUT /api/v1/games/{game_id}/details` but backend route is missing or not deployed.
   - **Impact:** VIP catalog management is blocked.
   - **Admin Workaround:** No admin-side workaround.
   - **Escalation Package:**
     - HTTP method + path: `PUT /api/v1/games/{game_id}/details`
     - Request sample: `{ "tags": ["VIP", "..."] }`
     - Expected vs actual: expected 200; actual 404
     - Logs keywords:
       - `games`
       - `details`
       - `404`
   - **Resolution Owner:** Backend
   - **Verification:** After fix, tag updates succeed and VIP list updates after refresh.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- VIP Games list updates after add/remove.
- Games page shows tags/status consistent.

### 8.2 System → Audit Log
- Look for catalog mutation events (naming varies): `game.updated`, `visibility.changed`.

### 8.3 System → Logs
- Check for errors/timeouts around games endpoints.

### 8.4 App / container logs
- Search keywords:
  - `games`
  - `vip`
  - `tags`
  - `/games/<id>/details`

### 8.5 DB audit (if available)
- Confirm game record tags for the intended tenant.
- Confirm audit trail in `auditevent`.

---

## 9) Security notes + rollback

- VIP misconfiguration can leak premium content or block VIP users.

Rollback (preferred):
1) Temporarily remove VIP tag (containment) or disable the game.
2) Confirm lobby enforcement logic.
3) Restore VIP tag once confirmed.

---

## 10) Related links

- Games: `/docs/new/en/admin/core/games.md`
- Feature Flags: `/docs/new/en/admin/system/feature-flags.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
