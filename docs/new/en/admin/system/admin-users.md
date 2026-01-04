# Admin Users (EN)

**Menu path (UI):** System → Admin Users  
**Frontend route:** `/admin` (tab: users)  
**Owner-only:** Yes  

---

## Ops Checklist (read first)

- Confirm tenant context: creating an admin in the wrong tenant is a security incident.
- Decide password mode: **manual** vs **invite**.
- For lockouts, use Password Reset runbook; for “no admins exist”, use Break-glass.
- Verify creation in UI and confirm evidence in Audit Log.

---

## 1) Purpose and scope

Admin Users manages administrative accounts for the current tenant, including creation and lifecycle status. This is a high-risk menu: it controls who can access the platform.

---

## 2) Who uses this / permission requirements

- Platform Owner (super admin) (recommended as the only actor in production).

---

## 3) Sub-sections / tabs

In the current UI (`frontend/src/pages/AdminManagement.jsx`):
- Users (Admin Users)
- Roles / Teams / Sessions / Invites / Security
- Activity Log / Permission Matrix / IP & Devices / Login History

This page is wide, but this document focuses on **Admin Users** core lifecycle.

---

## 4) Core workflows (step-by-step)

### 4.1 List admin users
1) Open System → Admin Users.
2) Ensure the active tab is **Users**.

**API calls (observed from frontend):**
- List: `GET /api/v1/admin/users`

### 4.2 Create an admin user (manual password)
1) Click **Create Admin User**.
2) Fill: full_name, email, role, tenant_role, tenant_id (if platform owner), password_mode=manual, password.
3) Submit.

**API calls:**
- Create: `POST /api/v1/admin/users`

### 4.3 Create an admin user (invite mode)
1) Choose password_mode=invite.
2) Submit.
3) Copy the invite link.

**Backend behavior:**
- Backend sets status `invited` and generates `invite_token`.

### 4.4 Enable/disable an admin
Backend supports:
- `POST /api/v1/admin/users/{admin_id}/status` body `{ is_active: true|false }`

**Important UI note:** AdminManagement.jsx currently does not call the status endpoint directly (in this build). If you need disable/enable and the UI has no control, treat it as a backend gap.

---

## 5) Field guide (practical tips)

- Use least privilege roles.
- Never share credentials.
- Use invite links with short validity and deliver over secure channels.

---

## 6) Common errors (Symptom → Likely cause → Fix → Verification)

1) **Symptom:** Cannot see users list.
   - **Likely cause:** role not owner; backend error.
   - **Fix:** use platform owner admin; check Network.
   - **Verification:** `GET /api/v1/admin/users` returns 200.

2) **Symptom:** Create user fails with USER_EXISTS.
   - **Likely cause:** email already exists.
   - **Fix:** use a different email; disable old user if needed.
   - **Verification:** create returns success.

3) **Symptom:** Invite created but link/token missing.
   - **Likely cause:** UI not showing res.data.invite_token.
   - **Fix:** check response payload; escalate if token omitted.
   - **Verification:** invite modal shows token.

4) **Symptom:** New admin can’t log in.
   - **Likely cause:** status invited/disabled; wrong password.
   - **Fix:** confirm status active and password correct; reset password if needed.
   - **Verification:** login succeeds.

5) **Symptom:** Wrong tenant admin created.
   - **Likely cause:** tenant_id selected incorrectly.
   - **Fix:** disable the admin immediately; create correct one.
   - **Verification:** audit evidence shows disable + correct creation.

6) **Symptom:** 403 TENANT_OVERRIDE_FORBIDDEN.
   - **Likely cause:** non-owner tried to create admin for another tenant.
   - **Fix:** use platform owner; do not bypass.
   - **Verification:** create succeeds with owner.

7) **Symptom:** Disable/enable action unavailable in UI.
   - **Likely cause:** UI missing control for `/status`.
   - **Fix:** escalate to frontend/back-end; use break-glass only if locked out.
   - **Verification:** after fix, UI toggles status.

8) **Symptom:** Audit evidence missing for user creation.
   - **Likely cause:** auditing disabled or failing.
   - **Fix:** check Audit Log; verify backend audit service.
   - **Verification:** `admin.user_created` event exists.

9) **Symptom:** Password reset needed.
   - **Likely cause:** user forgot password.
   - **Fix:** follow password reset runbook.
   - **Verification:** login succeeds after reset.

---

## 7) Backend/Integration Gaps (Release Note)

1) **Symptom:** UI shows Roles/Teams/Sessions/Invites tabs but endpoints return 404.
   - **Likely Cause:** UI calls `/api/v1/admin/roles`, `/teams`, `/sessions`, `/invites`, etc. Backend may not implement these routes.
   - **Impact:** Only Users tab works; advanced admin/security features are blocked.
   - **Admin Workaround:** No admin-side workaround.
   - **Escalation Package:**
     - Method + path: capture exact failing path from DevTools
     - Expected vs actual: expected 200; actual 404
     - Logs keywords: `admin/roles` / `admin/sessions` / `admin/invites`
   - **Resolution Owner:** Backend
   - **Verification:** endpoints return 200 and UI tabs populate.

---

## 8) Verification (UI + Logs + Audit + DB)

### 8.1 UI
- New admin appears in list.

### 8.2 System → Audit Log
- Look for:
  - `admin.user_created`
  - `admin.user_updated`
  - `admin.user_enabled` / `admin.user_disabled`

### 8.3 System → Logs / container logs
- Search for:
  - `admin.user_created`
  - email hash events
  - `TENANT_OVERRIDE_FORBIDDEN`

### 8.4 DB audit (if available)
- `adminuser` record exists with correct tenant_id and status.

---

## 9) Security notes + rollback

- Admin user creation is security-critical.
- Rollback:
  - disable the mistakenly created admin
  - rotate credentials if leak suspected

---

## 10) Related links

- Password reset: `/docs/new/en/runbooks/password-reset.md`
- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Audit Log: `/docs/new/en/admin/system/audit-log.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
