# Multi-Tenancy (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Backend Engineering  

This document explains tenant isolation and the rules that prevent cross-tenant access.

---

## 1) Tenant scope resolution

Tenant scope is resolved per request:
- Platform owner can impersonate using `X-Tenant-ID`
- Tenant admin cannot override tenant using headers

Reference:
- `backend/app/core/tenant_context.py`

---

## 2) Boundary guarantees

Guarantees expected:
- no cross-tenant reads/writes
- all audit/log records include tenant context

---

## 3) System tenant

Some deployments use a deterministic tenant id (e.g., `default_casino`) for boot/test.
This tenant should be protected from destructive operations.

---

## 4) Why tenant admins are constrained

Tenant admins are intentionally prevented from platform-level actions such as:
- creating tenants
- deleting/purging tenants

See:
- `/docs/new/en/admin/roles-permissions.md`
