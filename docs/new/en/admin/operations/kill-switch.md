# Kill Switch (EN)

**Menu path (UI):** Operations → Kill Switch  
**Frontend route:** `/kill-switch`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Confirm tenant + module scope before applying.
- Record reason + expected blast radius + rollback conditions.
- Verify blocked behavior (503) and collect evidence in **Audit Log**.
- Rollback as soon as safe: switch back to Enabled and verify endpoints recover.

---

## 1) Purpose and scope

Kill Switch provides an emergency control to disable specific modules per tenant (and optionally globally, depending on implementation). It is used to mitigate incidents (fraud waves, integration outages, runaway costs) by quickly blocking traffic.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) only.
- This menu is high-blast-radius and must be access-controlled.

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/KillSwitchPage.jsx`):
- Tenant selector
- Module selector (crm, affiliates, experiments, kill_switch)
- State selector (Enabled / Disabled)
- Apply

Backend routes:
- Status: `GET /api/v1/kill-switch/status`
- Set tenant module kill switch: `POST /api/v1/kill-switch/tenant`

---

## 4) Core workflows

### 4.1 Disable a module for a tenant
1) Confirm you are operating on the correct tenant.
2) Select the **Module** to disable.
3) Set state to **Disabled (503)**.
4) Click **Apply**.

**API calls (observed from frontend):**
- `POST /api/v1/kill-switch/tenant` body `{ tenant_id, module_key, disabled }`

### 4.2 Re-enable a module
1) Select the same tenant + module.
2) Set state to **Enabled**.
3) Apply.

### 4.3 Decision guide (when to use)
- Use kill switch when:
  - a module is causing financial loss, fraud exposure, or severe instability
  - a provider outage is causing cascading failures
- Do not use kill switch to “hide” routine bugs.

---

## 5) Field guide (practical tips)

- Always write down:
  - tenant
  - module
  - reason
  - expected blast radius
  - rollback conditions
- Apply the smallest possible scope (tenant + module).

**Do not:**
- Disable kill switch module itself unless you have a recovery plan.

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum 8 items (incident tooling).

1) **Symptom:** Kill switch left enabled after incident
   - Likely cause: missing post-incident checklist.
   - Fix: establish “disable/enable” checklist and an owner.
   - Verification: module is re-enabled; support ticket volume normalizes.

2) **Symptom:** Switched wrong tenant
   - Likely cause: tenant context confusion.
   - Fix: immediately revert; create an incident note.
   - Verification: audit evidence shows both the wrong change and the revert.

3) **Symptom:** Expected module did not stop
   - Likely cause: module gating not enforced in backend; cache.
   - Fix: confirm enforcement middleware exists; restart relevant services if needed.
   - Verification: blocked requests return 503 and logs show gating.

4) **Symptom:** Unexpected modules stopped (too broad impact)
   - Likely cause: wrong module_key or global switch applied.
   - Fix: revert to enabled; validate correct module.
   - Verification: unaffected modules resume normal traffic.

5) **Symptom:** Withdrawals stopped but deposits also stopped
   - Likely cause: wrong module key chosen or shared dependency.
   - Fix: adjust module scope; confirm module boundaries.
   - Verification: only intended endpoints are blocked.

6) **Symptom:** Admin access also impacted
   - Likely cause: kill switch enforced on admin routes or shared auth layer.
   - Fix: revert kill switch; if locked out, use break-glass.
   - Verification: admin UI accessible again.

7) **Symptom:** Apply returns 403
   - Likely cause: not platform owner or tenant feature disabled.
   - Fix: confirm role; verify tenant capabilities.
   - Verification: apply succeeds when performed by platform owner.

8) **Symptom:** Apply returns 200 but behavior doesn’t change
   - Likely cause: client caching; enforcement not applied downstream.
   - Fix: refresh affected clients; validate enforcement in backend.
   - Verification: blocked requests consistently return 503.

9) **Symptom:** No audit evidence for kill switch actions
   - Likely cause: auditing not implemented for this route.
   - Fix: ensure kill switch toggles are audited; temporarily use container logs as evidence.
   - Verification: System → Audit Log shows a kill switch event or logs provide timestamped proof.

---

## 7) Resolution steps (step-by-step)

1) Confirm incident severity and module scope.
2) Select tenant + module.
3) Apply Disabled.
4) Verify blocked behavior (503) and collect evidence.
5) Communicate to Support/CRM.
6) When stable, re-enable and verify recovery.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Kill switch control reflects the intended state.

### 8.2 System → Logs
- Search for blocked requests / 503 spikes.

### 8.3 App / container logs
- Search keywords:
  - `kill_switch`
  - `disabled` / `503`
  - module key (crm/affiliates/experiments)

### 8.4 System → Audit Log
- Expected audit events (naming varies): `kill_switch.toggled`.

### 8.5 Database audit (if present)
- Current implementation stores kill switches under `tenant.features.kill_switches` (JSON).
- Verify tenant features state matches the UI.

---

## 9) Security notes + rollback

- Kill switch is high blast radius.
- Rollback procedure (mandatory):
  1) Switch state back to Enabled.
  2) Verify endpoints resume.
  3) Ensure no residual client-side caching or blocked rules.

---

## 10) Related links

- Tenants (tenant selection safety): `/docs/new/en/admin/system/tenants.md`
- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
