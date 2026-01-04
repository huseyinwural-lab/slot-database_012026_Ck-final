# Admin Password Reset (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Security  

This document describes how admin password reset works in the current codebase and the recommended production approach.

---

## Current implementation (codebase behavior)

Endpoints:
- `POST /api/v1/auth/request-password-reset` (email)
- `POST /api/v1/auth/reset-password` (token + new_password)

Important:
- The system currently does **not** send email.
- The reset token is printed to server logs (best for dev, not for prod).

Operational flow:
1) Call `request-password-reset` for the admin email
2) Retrieve token from backend logs
3) Call `reset-password` with token

---

## Break-glass recovery (when no admins exist)

If `adminuser` table is empty, create the first Platform Owner (super admin) via DB.

Example (local/docker, idempotent):
- See the operational SQL script in legacy docs or your internal runbook.

Production guidance:
- Do not use a fixed password (e.g. `Admin123!`).
- Use a random secret injected via environment management.
- Log access to break-glass actions.
