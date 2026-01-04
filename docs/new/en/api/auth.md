# Auth API (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering  

---

## Admin login

- `POST /api/v1/auth/login`

Expected usage:
- Frontend posts `{ email, password }`.
- Response returns token / admin identity payload.

Rate limiting:
- Login is protected by rate limit middleware.
- See: `backend/app/middleware/rate_limit.py`

---

## Password reset

- `POST /api/v1/auth/request-password-reset`
- `POST /api/v1/auth/reset-password`

Important:
- Current code prints reset token to logs (dev-oriented).
- Production should use an email delivery provider.

See:
- `/docs/new/en/runbooks/password-reset.md`
