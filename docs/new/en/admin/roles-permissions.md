# Roles & Permissions (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Security / Platform Engineering  

This document explains the **role model** and the **enforcement points** used by the backend.

---

## 1) Terminology

- **Platform Owner (Super Admin):** `AdminUser.is_platform_owner = true`
- **Tenant Admin:** typically `AdminUser.tenant_role = "tenant_admin"` bound to a single `tenant_id`
- **Tenant scope:** the active tenant context resolved for a request.

---

## 2) Role → capability matrix

| Capability | Platform Owner | Tenant Admin | Notes |
|---|---:|---:|---|
| List tenants | ✅ | ❌ | Owner-only (`require_owner`) |
| Create tenant | ✅ | ❌ | Owner-only (`require_owner`) |
| Update tenant feature flags | ✅ | ❌ | Owner-only (`require_owner`) |
| Read tenant capabilities | ✅ | ✅ | Tenant is resolved by `get_current_tenant_id()` |
| Update payments policy (tenant) | ✅ | ✅ | Allowed via `require_tenant_policy_admin` |
| Impersonate tenant via `X-Tenant-ID` | ✅ | ❌ | Forbidden for non-owners |

---

## 3) Where enforcement happens (code pointers)

### 3.1 Owner-only guard

- `backend/app/utils/permissions.py`
  - `require_owner(admin)`

Used by (examples):
- `backend/app/routes/tenant.py`
  - `GET /api/v1/tenants` (list) → owner-only
  - `POST /api/v1/tenants` (create) → owner-only
  - `PATCH /api/v1/tenants/{tenant_id}` (feature flags) → owner-only

### 3.2 Tenant scope resolution guard

- `backend/app/core/tenant_context.py`
  - `get_current_tenant_id(request, current_admin, session)`

Rules:
- `X-Tenant-ID` header is allowed **only** when `is_platform_owner=true`.
- Non-owner sending `X-Tenant-ID` → **403 TENANT_HEADER_FORBIDDEN**.

### 3.3 Tenant-admin allowed policy updates

- `backend/app/routes/tenant.py`
  - `require_tenant_policy_admin(admin)`
  - `PUT /api/v1/tenants/payments/policy`

---

## 4) Why tenant admin cannot delete tenants

Tenant deletion/purge is a platform-level destructive operation:
- It can impact data retention/audit requirements.
- It can break deterministic test/system tenants (e.g. `default_casino`).
- It is intentionally restricted to Platform Owner.

If you add tenant delete/purge endpoints in the future:
- guard them with `require_owner`
- add explicit protection for system tenants
- audit log every action
