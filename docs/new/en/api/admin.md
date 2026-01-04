# Admin API (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering  

This document outlines admin-facing API areas (admin users, tenant administration, and related governance surfaces).

---

## 1) Base path

Typical admin paths:
- `/api/v1/admin/*`

---

## 2) Authorization model

- Platform Owner (Super Admin): `is_platform_owner = true`
- Tenant Admin: `tenant_role = tenant_admin` (tenant-scoped)

Rules:
- Owner-only operations must use `require_owner()`.
- Tenant scope is resolved via `get_current_tenant_id()`.
- `X-Tenant-ID` header is allowed only for owner impersonation.

See:
- `/docs/new/en/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
- `backend/app/utils/permissions.py`

---

## 3) Admin user management (typical)

The exact endpoints may vary by deployment, but admin modules usually include:
- Creating/inviting tenant admins
- Listing admins within a tenant scope
- Disabling/enabling admin accounts

> Ops note: destructive operations (disable/delete) should be audited.

---

## 4) Audit & traceability

Admin operations should emit audit events for:
- admin created/invited
- admin disabled/enabled
- failed login attempts / lockouts
- break-glass creation of first owner

Legacy references:
- `/docs/ops/log_schema.md`
- `/docs/ops/audit.md` (if present)
