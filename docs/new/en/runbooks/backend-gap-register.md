# Backend Gap Register (EN)

**Last reviewed:** 2026-01-05  
**Owner:** Platform Engineering / Ops  

This register centralizes **UI ↔ Backend mismatches** discovered while writing the Admin Panel Manual.

**How to use:**
- Each entry must be **closeable** (owner + SLA + verification).
- Keep EN/TR files mirrored (see `/docs/new/tr/runbooks/backend-gap-register.md`).
- Status flow: **Open → In Progress → Fixed → Verified**.

---

## Triage Summary (Ops)

| ID | Area | Gap | Priority | Owner | SLA | Target Version | Status | Workaround | Verification |
|---:|------|-----|----------|-------|-----|---------------|--------|------------|-------------|
| G-001 | Games | Import returns 404 | P1 | Backend | 7d | TBD | Open | Use manual config / avoid import | Endpoint returns 200; UI import succeeds |
| G-002 | System → API Keys | Toggle/patch returns 404 | P1 | Backend | 7d | TBD | Open | No safe workaround (keep keys static) | Patch returns 200; UI toggle persists |
| G-003 | Reports / Simulator | Reports endpoints + simulator runs are stub/404 | P1 | Backend | 7d | TBD | Open | Export-only / manual analysis | Report endpoints return data; simulator run endpoints exist |

> SLA default: P0=24h, P1=7d, P2=30d.

---


> This register complements the per-menu “Backend/Integration Gaps” sections.
> When a gap is confirmed, add it here as the actionable tracking item.

## 1) Open gaps (by module)

### 1.1 Core → Games → Manual import endpoints return 404

- **ID:** G-001
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

- **Source page:** `/docs/new/en/admin/core/games.md`
- **Symptom:** Game manual upload / preview / confirm import flow fails with **404 Not Found**.
- **UI endpoints:**
  - `POST /api/v1/game-import/manual/upload`
  - `GET /api/v1/game-import/jobs/{job_id}`
  - `POST /api/v1/game-import/jobs/{job_id}/import`
- **Impact:** Catalog ingestion is blocked in this environment.
- **Admin Workaround:** No admin-side workaround; defer import until backend supports these routes.
- **Escalation Package:**
  - Capture 404 from DevTools Network for the above endpoints
  - Expected vs actual: 200 + `{ job_id }` vs 404
  - Keywords: `game-import`, `import`
- **Verification (done when fixed):** Upload returns 200 with `job_id`; job fetch returns 200; confirm import returns 200; UI completes the import.

---

### 1.2 System → API Keys → Toggle endpoint returns 404

- **ID:** G-002
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

- **Source page:** `/docs/new/en/admin/system/api-keys.md`
- **Symptom:** Toggling key status fails with **404 Not Found**.
- **UI endpoint:** `PATCH /api/v1/api-keys/{id}` body `{ active: true|false }`
- **Impact:** Keys cannot be disabled/reenabled safely; incident response and rotation procedures are weakened.
- **Admin Workaround:** Treat keys as static; rotate by creating a new key and revoking via secret manager (if supported externally).
- **Escalation Package:**
  - Capture 404 from DevTools Network for `PATCH /api/v1/api-keys/{id}`
  - Expected vs actual: 200 vs 404
  - Keywords: `api-keys`, `PATCH`
- **Verification (done when fixed):** Patch returns 200; UI shows visible toggle change; state persists after refresh.

---

### 1.3 System → Reports / Simulator → Endpoints are stubbed or missing

- **ID:** G-003
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

- **Source pages:**
  - `/docs/new/en/admin/system/reports.md`
  - `/docs/new/en/admin/system/simulator.md`
- **Symptom:** Reports pages return empty/stub data or 404; simulator actions do not persist runs.
- **Likely Cause:** `/api/v1/reports/*` and simulator run endpoints are not fully implemented in this build.
- **UI endpoints (examples):**
  - `GET /api/v1/reports/overview` (and other tabs)
  - `POST /api/v1/reports/exports`
  - (simulator) run endpoints vary by module
- **Admin Workaround:** Use export-only if available; otherwise manual analysis from DB/logs.
- **Escalation Package:**
  - Capture the first failing path(s) from DevTools Network
  - Expected vs actual: 200 with data vs 404/empty
  - Keywords: `reports`, `exports`, `simulator`
- **Verification (done when fixed):** Report endpoints return non-empty data where applicable; export job returns 200; simulator runs are created and listed.

---


### 1.4 System → Logs → Category endpoints return empty lists

- **ID:** G-004
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

- **Source page:** `/docs/new/en/admin/system/logs.md`
- **Symptom:** Most tabs return `[]` / show “No logs found” even during known incidents.
- **Likely Cause:** `backend/app/routes/logs.py` implements `/events` but many category endpoints are stubbed or return empty arrays.
- **Impact:** Ops cannot rely on the Logs UI for evidence; must pivot to container logs.
- **Admin Workaround:**
  - Use **System Events** as primary.
  - For cron/deployments/db/cache: use container logs / infra monitoring.
- **Escalation Package:**
  - `GET /api/v1/logs/<category>` (cron/health/deployments/config/errors/queues/db/cache/archive)
  - Expected vs actual: meaningful events vs `[]`
  - Keywords: `logs/<category>`
- **Resolution Owner:** Backend
- **Verification (done when fixed):** Each category endpoint returns non-empty events when events exist; UI tabs populate.

---

### 1.5 System → Admin Users → Non-Users tabs appear but endpoints may be missing

- **ID:** G-005
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** High

- **Source page:** `/docs/new/en/admin/system/admin-users.md`
- **Symptom:** UI shows Roles/Teams/Sessions/Invites/Security tabs, but requests return **404 Not Found**.
- **Likely Cause:** UI calls endpoints like `/api/v1/admin/roles`, `/api/v1/admin/sessions`, `/api/v1/admin/invites` which are not implemented.
- **Impact:** Only basic Admin Users lifecycle works; advanced security/admin ops are blocked.
- **Admin Workaround:** No admin-side workaround.
- **Escalation Package:**
  - Capture the exact failing paths from DevTools Network
  - Expected vs actual: 200 vs 404
  - Keywords: `admin/roles`, `admin/sessions`, `admin/invites`
- **Resolution Owner:** Backend
- **Verification (done when fixed):** Tab endpoints exist and return 200 with data; UI tabs populate.

---

### 1.6 System → Feature Flags → Safe stubs (no persistence)

- **ID:** G-006
- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
- **Owner:** Backend
- **SLA:** 7d
- **Target Version:** TBD
- **Impact:** Medium

- **Source page:** `/docs/new/en/admin/system/feature-flags.md`
- **Symptom:** Flags always return empty lists / toggles return OK but do not persist.
- **Likely Cause:** `/api/v1/flags/*` routes implemented as safe stubs (return `[]` / return OK) in this build.
- **Impact:** Feature Flags cannot be used for production-grade rollouts.
- **Admin Workaround:**
  - Use **Operations → Kill Switch** for incident gating.
  - Treat Feature Flags as informational until persistence is implemented.
- **Escalation Package:**
  - `GET /api/v1/flags/`, `POST /api/v1/flags/`, `POST /api/v1/flags/{id}/toggle`
  - Expected vs actual: persisted state vs no persistence / empty
  - Keywords: `flags`, `toggle`
- **Resolution Owner:** Backend
- **Verification (done when fixed):** Toggle persists across refresh; list reflects new state.

---

## 2) Notes / process

- When you identify a new gap, add:
  - menu/module
  - exact endpoint
  - evidence link/ref (optional)
  - impact severity (P0/P1/P2)
  - customer impact (optional)
- Keep the register short and actionable; deep analysis belongs in engineering tickets.
