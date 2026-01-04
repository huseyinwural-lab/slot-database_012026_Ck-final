# Tenants API (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering  

---

## Owner-only endpoints

- `GET /api/v1/tenants` — list tenants
- `POST /api/v1/tenants` — create tenant
- `PATCH /api/v1/tenants/{tenant_id}` — update tenant feature flags

Enforced by:
- `require_owner()`
- `backend/app/utils/permissions.py`

---

## Tenant-scoped endpoints

- `GET /api/v1/tenants/capabilities`
- `GET /api/v1/tenants/payments/policy`
- `PUT /api/v1/tenants/payments/policy`

Tenant resolution:
- Owner can override via `X-Tenant-ID` (impersonation)
- Non-owner header usage is forbidden

See:
- `/docs/new/en/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
