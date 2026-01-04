# Backend Gap Register (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering / Ops  

This register centralizes **UI ↔ Backend mismatches** discovered while writing the Admin Panel Manual.

**How to use:**
- Each entry should be **actionable** (symptom + impact + workaround + escalation evidence).
- Treat this file as the single backlog source for closing product gaps.
- Keep EN/TR files mirrored (see `/docs/new/tr/runbooks/backend-gap-register.md`).

---


> This register complements the per-menu “Backend/Integration Gaps” sections.
> When a gap is confirmed, add it here as the actionable tracking item.

## 1) Open gaps (by module)

### 1.1 System → Logs → Category endpoints return empty lists

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
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

### 1.2 System → Admin Users → Non-Users tabs appear but endpoints may be missing

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1
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

### 1.3 System → Feature Flags → Safe stubs (no persistence)

- **First Seen:** 2026-01-04
- **Environment:** all
- **Status:** Open
- **Priority:** P1

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
