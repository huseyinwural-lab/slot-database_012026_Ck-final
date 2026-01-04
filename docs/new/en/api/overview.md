# API Overview (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering  

This section provides a lightweight map of key API areas. Detailed endpoint specs may evolve; this is meant to stay stable.

---

## Base path

All backend endpoints are mounted under:
- `/api/v1/...`

---

## Key areas

- Auth: `/api/v1/auth/*`
- Tenants: `/api/v1/tenants/*`
- Admin (tenant admin management, etc.): `/api/v1/admin/*` (see `admin.md`)
- Payments: `/api/v1/payments/*` (see `payments.md`)
- Payouts: `/api/v1/payouts/*` (see `payouts.md`)

---

## Multi-tenancy rules

- Tenant context is derived from the logged-in admin (`tenant_id`).
- Platform owner may impersonate tenant scope via `X-Tenant-ID` header.
- Non-owners must not use `X-Tenant-ID`.

Implementation reference:
- `backend/app/core/tenant_context.py`
