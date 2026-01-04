# Tenants (EN)

**Menu path (UI):** System → Tenants  
**Frontend route:** `/tenants`  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Confirm **tenant id + name** before any save.
- Any destructive operation: confirm rollback path (**disable reversible**, purge usually not).
- Verify changes in UI and in **System → Audit Log**.
- For incidents: capture request path + status code + `request_id` (if present).

---

## 1) Purpose and scope

The Tenants menu is the platform owner’s control surface for managing tenant lifecycle: creating tenants, viewing existing tenants, and updating tenant feature flags and menu visibility flags.

> This is one of the highest-risk menus: a wrong-tenant action can affect production operations and security boundaries.

---

## 2) Who uses this / permission requirements

- **Platform Owner (super admin) only.**
- Tenant admins must not have access.

---

## 3) Sub-sections / functional areas

In the current UI (`frontend/src/pages/TenantsPage.jsx`):
- Tenant list (paged)
- Tenant create (name, type, features)
- Tenant feature edit (feature flags)
- Tenant menu visibility flags edit (menu_flags)

Backend enforcement is also owner-only:
- `GET /api/v1/tenants/` requires owner.

---

## 4) Core workflows

### 4.1 Create a new tenant (Platform Owner only)
1) Open System → Tenants.
2) Fill **Tenant name** and **type**.
3) Select default **features** (can_use_game_robot, can_edit_configs, can_manage_bonus, can_view_reports).
4) Submit.

**Hard-stop permission rule (backend):**
- If `current_admin.is_platform_owner != true` → **403 Forbidden**.

**Audit (mandatory):**
- `tenant.create.attempt` is written for **all attempts** (success, failed, denied).
- `tenant.created` is written for successful creations.

**API calls (observed from frontend):**
- Create: `POST /api/v1/tenants/`

### 4.2 View tenant list
1) Open tenant list.
2) Use pagination controls (Previous/Next).

**API calls:**
- List: `GET /api/v1/tenants/?page=<n>&page_size=<n>`

### 4.3 Update tenant features
1) Click **Edit Features** for a tenant.
2) Toggle features.
3) Save.

**API calls:**
- Update: `PATCH /api/v1/tenants/{tenant_id}` with `{ features: {...} }`

### 4.4 Update menu visibility flags (menu_flags)
This controls which sidebar menu items are hidden/shown per tenant.

1) In edit mode, toggle menu flags.
2) Save.

**Notes:**
- UI logic treats `menu_flags[key] === false` as hidden. Default is “enabled”.

---

## 5) Field guide (practical tips)

- Always verify you are editing the correct tenant (name + id).
- Use feature flags as a hard contract for tenant entitlements.
- When changing menu flags, coordinate with Support/Operations so they know what is intentionally hidden.

**Do not:**
- Remove access to Audit/Logs/Keys during an active incident.

---

## 6) Common errors (symptom → likely cause → fix → verification)

> Minimum 8 items (high-risk operational surface).

1) **Symptom:** “Tenant cannot be created”
   - Likely cause: missing required fields, duplicate tenant name.
   - Fix: verify `name` non-empty; choose a unique name.
   - Verification: `POST /api/v1/tenants/` returns 200 and tenant appears in list.

2) **Symptom:** Tenants list is empty / incomplete
   - Likely cause: not platform owner; backend error.
   - Fix: confirm admin is platform owner; check Network for `GET /api/v1/tenants/`.
   - Verification: list endpoint returns items and meta.

3) **Symptom:** Wrong-tenant changes were applied
   - Likely cause: operator selected the wrong tenant row.
   - Fix: immediately revert the changes on the correct tenant; create an incident note.
   - Verification: compare before/after state in Audit Log and tenant features.

4) **Symptom:** Tenant disabled but users still can access
   - Likely cause: disable not implemented; session/token caching; the change was only UI-level.
   - Fix: verify actual backend enforcement exists; force session invalidation if supported.
   - Verification: affected user receives 401/403 on protected endpoints.

5) **Symptom:** Attempt to delete/purge a system tenant
   - Likely cause: operator mistake.
   - Fix: do not proceed; follow guardrails (expected behavior is 403/blocked).
   - Verification: action is blocked and recorded as attempted/denied in audit (if implemented).

6) **Symptom:** Tenant purge triggered by mistake
   - Likely cause: unsafe UI flow or lack of confirmation.
   - Fix: treat as incident; if purge is irreversible, follow backup/restore procedure.
   - Verification: confirm data presence/absence in DB; produce evidence.

7) **Symptom:** Tenant admin cannot log in
   - Likely cause: admin user not assigned to tenant; role misconfigured; tenant features disabled for required module.
   - Fix: check Admin Users; verify tenant_id + roles.
   - Verification: login works and capabilities endpoint reflects correct tenant.

8) **Symptom:** “Tenant features updated” but UI behavior doesn’t change
   - Likely cause: capabilities cached client-side; menu flags logic defaulting; refresh needed.
   - Fix: refresh browser; re-fetch capabilities.
   - Verification: `GET /api/v1/tenants/capabilities` shows updated features; menus appear/disappear as expected.

9) **Symptom:** Reports still show after tenant changes
   - Likely cause: report caching/retention.
   - Fix: confirm cache TTL; regenerate reports.
   - Verification: reports reflect latest tenant state.

---

## 7) Resolution steps (step-by-step)

1) Capture Network evidence (endpoint + status + payload).
2) Confirm the acting admin is platform owner.
3) Validate tenant id/name before saving.
4) If a wrong change happened: revert immediately and record in incident/audit evidence pack.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- Tenant appears in list after create.
- Feature toggles persist after refresh.
- Menu flags change the sidebar visibility for the tenant.

### 8.2 System → Logs
- Check for errors around tenants update calls.

### 8.3 App / container logs
- Search keywords:
  - `tenants`
  - `TENANT_EXISTS` / `TENANT_NOT_FOUND`
  - `capabilities`

### 8.4 System → Audit Log
- Expected actions (observed in backend code):
  - `tenant.created`
  - `tenant.feature_flags_changed`
  - `TENANT_POLICY_UPDATED` (payments policy)

### 8.5 Database audit (if present)
- Canonical tables:
  - `tenant` (features JSON)
  - `auditevent` (tenant lifecycle changes)

---

## 9) Security notes + rollback (mandatory)

### 9.1 System tenant protection (critical)
- The **system tenant must be protected** in both UI and backend.
- Expected guarantees:
  - it cannot be hard-deleted via UI
  - any attempt should be blocked and auditable

### 9.2 Rollback rules
- **Disable** can be reverted (re-enable) if implemented.
- **Purge/hard delete** (if present) is typically irreversible.
  - For recovery, use backup/restore procedures (see Ops manual).

---

## 10) Related links

- Admin Users (tenant admin assignment): `/docs/new/en/admin/system/admin-users.md`
- Break-glass (if all admins locked out): `/docs/new/en/runbooks/break-glass.md`
- Backup/restore policy: `/docs/new/en/guides/ops-manual.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
