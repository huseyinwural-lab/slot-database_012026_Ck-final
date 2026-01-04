# Feature Flags (EN)

**Menu path (UI):** System → Feature Flags  
**Frontend route:** `/experiments`  
**Owner-only:** Yes (owner + module access `experiments`)  

---

## Ops Checklist (read first)

- Before toggling: confirm **tenant context** and confirm you understand blast radius.
- For rollouts: prefer **small percentage** first (or a controlled segment) and monitor error rate.
- If the flag effect is not visible: refresh, check cache propagation, and confirm backend endpoint returned success.
- If a wrong flag breaks production: rollback immediately (toggle off) and capture audit evidence.

---

## 1) Purpose and scope

Feature Flags provides runtime control over feature exposure (enable/disable), experiments, and targeting. It is used for controlled rollouts, incident mitigation, and staged releases.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin)
- Requires module access: `experiments` (enforced on backend)

---

## 3) Sub-sections / tabs

In the current UI (`frontend/src/pages/FeatureFlags.jsx`):
- Feature Flags
- Experiments
- Segments
- Analytics
- Results
- Audit Log (flags)
- Env Compare
- Groups

Backend routes used by UI:
- `GET /api/v1/flags/`
- `POST /api/v1/flags/` (create)
- `POST /api/v1/flags/{flag_id}/toggle`
- `GET /api/v1/flags/experiments`
- `POST /api/v1/flags/experiments/{id}/start|pause`
- `GET /api/v1/flags/segments`
- `GET /api/v1/flags/audit-log`
- `GET /api/v1/flags/environment-comparison`
- `GET /api/v1/flags/groups`
- `POST /api/v1/flags/kill-switch`

---

## 4) Rollout and targeting model (how to think about it)

This UI supports a “product-style” feature flag model:
- Percentage rollout (gradual exposure)
- Segment-based exposure (controlled cohorts)

Operational guidance:
- Start with a segment or low percentage.
- Monitor KPIs/errors.
- Expand gradually.

---

## 5) Core workflows (step-by-step)

### 5.1 Toggle a flag
1) Open Feature Flags tab.
2) Click the power icon on a flag.

**API calls:**
- Toggle: `POST /api/v1/flags/{flag_id}/toggle`

### 5.2 Kill switch (flags)
1) Click **Kill Switch**.
2) Confirm.

**API calls:**
- `POST /api/v1/flags/kill-switch`

### 5.3 Create a flag
1) Click **Create Flag**.
2) Enter flag_id, name, description, type, scope, environment, group.
3) Save.

**API calls:**
- Create: `POST /api/v1/flags/`

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** “Flag effect is not visible”.
   - **Likely cause:** cache/propagation delay; client needs reload.
   - **Fix:** refresh; wait TTL; verify downstream services reloaded.
   - **Verification:** behavior changes after refresh and consistent across sessions.

2) **Symptom:** Toggling returns success but nothing changes.
   - **Likely cause:** backend is stubbed (no persistence).
   - **Fix:** treat as backend gap; do not rely on it for production gating.
   - **Verification:** after backend fix, list reflects changed status.

3) **Symptom:** Wrong flag breaks production.
   - **Likely cause:** unsafe rollout; missing staging validation.
   - **Fix:** rollback immediately (toggle off); communicate; create incident.
   - **Verification:** error rate drops and behavior returns.

4) **Symptom:** 403 Forbidden.
   - **Likely cause:** not platform owner or tenant lacks `experiments` module.
   - **Fix:** use owner admin; enable module in tenant settings.
   - **Verification:** endpoints return 200.

5) **Symptom:** Cannot load any flags.
   - **Likely cause:** endpoint error or auth.
   - **Fix:** check `/api/v1/flags/` response.
   - **Verification:** list loads.

6) **Symptom:** Env Compare is empty.
   - **Likely cause:** stub endpoint or no data.
   - **Fix:** treat as informational; escalate if needed.
   - **Verification:** compare endpoint returns differences.

7) **Symptom:** Segments list is empty.
   - **Likely cause:** segments not implemented.
   - **Fix:** treat as backend gap.
   - **Verification:** segments endpoint returns list.

8) **Symptom:** Audit tab empty.
   - **Likely cause:** audit-log endpoint stub.
   - **Fix:** use System → Audit Log as canonical evidence.
   - **Verification:** `auditevent` contains flag actions.

9) **Symptom:** Kill switch button returns OK but does nothing.
   - **Likely cause:** backend keeps this endpoint as no-op.
   - **Fix:** use Operations → Kill Switch for real gating.
   - **Verification:** module kill switch blocks requests.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** Flags do not persist / always return empty lists.
   - **Likely Cause:** backend `/api/v1/flags/*` routes are implemented as safe stubs (return `[]`, return OK) in this build.
   - **Impact:** Feature Flags UI cannot be used as a production-grade rollout mechanism.
   - **Admin Workaround:**
     - Use Operations → Kill Switch for incident gating.
     - Treat Feature Flags as informational until persistence is implemented.
   - **Escalation Package:**
     - HTTP method + path: `GET /api/v1/flags/`, `POST /api/v1/flags/`, `POST /api/v1/flags/{id}/toggle`
     - Expected vs actual: expected persisted state; actual no persistence / empty
     - Logs keywords: `flags`, `toggle`, `CREATED`, `TOGGLED`
   - **Resolution Owner:** Backend
   - **Verification:** toggles persist and list reflects status across reload.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Flag list loads.
- Toggle action shows a state change (if persistence exists).

### 8.2 System → Audit Log
- Look for actions related to flags (if implemented).

### 8.3 System → Logs / container logs
- Search keywords: `flags`, `toggle`, `experiments`.

### 8.4 DB audit (if available)
- Check `featureflag` / `feature_flags` tables (if implemented) and `auditevent`.

---

## 9) Security notes + rollback

- Wrong flags can break production. Rollback must be immediate.

---

## 10) Related links

- Kill Switch: `/docs/new/en/admin/operations/kill-switch.md`
- Tenants: `/docs/new/en/admin/system/tenants.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
