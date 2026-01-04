# Password Reset (EN) — Runbook

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Security  

This runbook defines the deterministic **password reset procedure** for Admin users (and, if applicable, for Players).

> This is an operational procedure (runbook). UI menu pages should link here instead of duplicating step-by-step reset instructions.

---

## 0) Scope

### In scope
- Admin password reset (current implementation)
- Where to find evidence (logs/audit)
- Break-glass reference for “no admins exist” scenario

### Out of scope
- Email delivery / SMTP provider integration (not implemented here)

---

## 1) Admin password reset — current codebase behavior

### 1.1 Endpoints
- Request reset token:
  - `POST /api/v1/auth/request-password-reset`
  - Body: `{ "email": "admin@example.com" }`
- Confirm reset:
  - `POST /api/v1/auth/reset-password`
  - Body: `{ "token": "...", "new_password": "..." }`

### 1.2 Important constraints
- The system currently does **not send email**.
- The reset token is printed to backend logs (acceptable for dev/test, risky for prod).
- Token expiry: ~30 minutes (JWT).

### 1.3 Procedure (step-by-step)
1) Trigger reset token creation
   - Call `POST /api/v1/auth/request-password-reset` with the admin email.
   - Expected response: generic success message (prevents user enumeration).

2) Retrieve the reset token from backend logs
   - Search in backend/container logs for:
     - `[Password Reset] Token for` (exact prefix)
     - admin email
   - Copy the token.

3) Reset the password
   - Call `POST /api/v1/auth/reset-password` with:
     - `token` (from logs)
     - `new_password`
   - Expected response: success JSON.

4) Verify
   - Attempt login via:
     - `POST /api/v1/auth/login`
   - Confirm the user can authenticate and access required menus.

---

## 2) Evidence & verification (UI + Logs + DB)

### 2.1 UI (preferred)
- System → Audit Log
  - Filter by timeframe and actor (if available)
  - Note: password reset may not be audited depending on implementation.

### 2.2 Backend / container logs
- Search keys:
  - admin email
  - `[Password Reset] Token for` (token emission)
  - `x-request-id` (if captured from response headers)

### 2.3 Database (if you need hard evidence)
- Table: `adminuser`
  - `password_reset_token` should match the token until reset completes.
  - After successful reset, `password_hash` changes.

---

## 3) Failure modes and fixes

1) **Symptom:** Reset token not found in logs
   - Likely cause: wrong environment / wrong log target
   - Fix: check correct backend instance logs; re-run request step.

2) **Symptom:** `RESET_TOKEN_INVALID` / token mismatch
   - Likely cause: expired token or a newer token overwrote the previous one
   - Fix: re-run request step; use newest token.

3) **Symptom:** Reset succeeds but login still fails
   - Likely cause: admin disabled (`is_active=false` or `status!=active`)
   - Fix: re-enable the admin (Admin Users page) or via DB under break-glass change control.

---

## 4) Break-glass (no admins exist)

If no admins exist (or all are locked out), follow break-glass process:
- `/docs/new/en/runbooks/break-glass.md`

