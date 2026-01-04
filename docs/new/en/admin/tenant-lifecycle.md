# Tenant Lifecycle (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Owner / Ops  

Goal: A production-safe flow where **Platform Owner (Super Admin)** creates tenants and delegates tenant administration.

---

## Concepts

- **Platform Owner (Super Admin):** `AdminUser.is_platform_owner = true`
- **Tenant:** isolated scope for games, finance, settings, admins, players
- **Tenant Admin:** an admin user bound to a specific tenant

---

## Recommended lifecycle

1) Platform Owner logs in
2) Platform Owner creates a Tenant
3) Platform Owner creates (or invites) a Tenant Admin
4) Tenant Admin configures operations (payments, limits, staff)

---

## Notes for testing

In some CI/E2E paths, the system uses a deterministic tenant id like `default_casino`.
That is a testing convenience and does not replace the production lifecycle above.

Legacy reference:
- `/docs/TENANT_ADMIN_FLOW.md`
- `/docs/manuals/PLATFORM_OWNER_GUIDE.md`
- `/docs/manuals/TENANT_ADMIN_GUIDE.md`
