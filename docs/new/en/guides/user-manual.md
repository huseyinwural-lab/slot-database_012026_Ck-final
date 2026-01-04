# User Manual (EN) — Operations-Ready

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering / Ops  

This is the **operations-grade, long-lived** manual intended to be enough for a new engineer to run the system without tribal knowledge.

> EN is the **source of truth**. TR is a mirror under `/docs/new/tr/guides/user-manual.md`.

---

## Table of contents

1. Install
2. Environments (dev / stage / prod)
3. Authorization & Role Model (Access Control)
4. Admin Login & Tenant Lifecycle (platform owner → tenant → tenant admin)
5. Tenant Security & Isolation Guarantees
6. Data Lifecycle
7. CI / Release Runbook
8. Upgrade / Migration Guide
9. Configuration & Secrets Management
10. Logging, Audit & Traceability
11. Password Reset & Break-Glass
12. Common Errors & Fixes
13. Performance & Guardrails
14. Support & Incident Flow

---

## 1) Install

See:
- `/docs/new/en/guides/install.md`

---

## 2) Environments (dev / stage / prod)

See:
- `/docs/new/en/guides/deployment.md`

---

## 3) Authorization & Role Model (Access Control)

### 3.1 Role definitions (current codebase)

The admin identity model is centered around `AdminUser`:
- `is_platform_owner` — **TRUE**: platform owner / super admin (cross-tenant visibility)
- `tenant_id` — tenant scope for a non-owner admin
- `tenant_role` — role within a tenant (default often `tenant_admin`)

Relevant implementation references:
- `backend/app/models/sql_models.py` (fields)
- `backend/app/utils/permissions.py` (`require_owner`)
- `/docs/new/en/admin/roles-permissions.md` (role matrix + enforcement pointers)

### 3.2 Role & capability matrix

| Role | Scope | Tenant create | Tenant delete/purge | Tenant policy update | Read audit | Notes |
|---|---|---:|---:|---:|---:|---|
| Platform Owner (Super Admin) | All tenants | ✅ | ✅ (guarded) | ✅ | ✅ | Can impersonate tenant via `X-Tenant-ID` header (owner-only) |
| Tenant Admin | One tenant | ❌ | ❌ | ✅ | ✅ (tenant-scoped) | `X-Tenant-ID` header forbidden |

> Why tenant admin cannot delete tenants:
> - Tenant deletion/purge is a platform-level destructive operation.
> - In code, tenant creation/listing and owner-only edits are protected by `require_owner()`.

### 3.3 Endpoint-level enforcement (examples)

- Tenants endpoints are owner-only for create/list and some mutations:
  - `POST /api/v1/tenants` → `require_owner(current_admin)`
  - `GET /api/v1/tenants` → `require_owner(current_admin)`

- Tenant-admin allowed for policy update (tenant-scoped):
  - `PUT /api/v1/tenants/payments/policy` → `require_tenant_policy_admin`

---

## 4) Admin Login & Tenant Lifecycle

See:
- `/docs/new/en/admin/tenant-lifecycle.md`

Also important tenant-scope behavior:
- `X-Tenant-ID` header is allowed **only** for platform owner impersonation.
- Tenant admins cannot override tenant via header.

Implementation reference:
- `backend/app/core/tenant_context.py`

---

## 5) Tenant Security & Isolation Guarantees

### 5.1 Tenant ID propagation

Tenant scope should flow:
- Request → `X-Tenant-ID` (optional, owner-only)
- Backend → `get_current_tenant_id()`
- DB queries → filter by `tenant_id` / use resolved tenant context
- Logs/audit → include `tenant_id` and `request_id`

### 5.2 Cross-tenant leakage prevention

Primary guardrails:
- Tenant scope resolution logic forbids tenant header injection for non-owners.
- Routes use `get_current_tenant_id()` before querying tenant-scoped resources.

### 5.3 Why system tenant should not be deleted

Many tests and deterministic boot paths rely on a stable tenant id (commonly `default_casino`).
Production should treat the “system tenant” as protected.

> If you implement hard delete/purge, you must add explicit guards for system tenants.

### 5.4 Soft delete vs hard delete

- **Soft delete:** record remains, marked as deleted/inactive
- **Hard delete:** record physically removed

In a casino/finance context, prefer soft delete for auditability.

---

## 6) Data Lifecycle

### 6.1 Retention & purge

Legacy references:
- `/docs/ops/backup.md`
- `/docs/ops/dr_runbook.md`
- `/docs/ops/restore_drill_proof/template.md`

Key principles:
- Deletion ≠ erasure (audit/finance)
- Purge must be controlled and logged
- Backup/restore impacts retention and tenant removal operations

### 6.2 What happens when a tenant is disabled/deleted?

This depends on implementation.
At minimum, document:
- which tables are tenant-scoped
- whether deletes are soft/hard
- which background jobs still run

---

## 7) CI / Release Runbook

See:
- `/docs/new/en/runbooks/ci.md`

---

## 8) Upgrade / Migration Guide

### 8.1 Order of operations

Recommended order:
1) Deploy app code
2) Run DB migrations (`alembic upgrade head`)
3) Smoke test critical flows

### 8.2 Rollback strategy

- App rollback (container/image)
- DB rollback is harder; prefer restore-from-backup when integrity is in doubt

Legacy reference:
- `/docs/ops/dr_runbook.md`

### 8.3 If migration fails

Immediate actions:
- Stop further deploy steps
- Capture migration logs
- Decide: hotfix migration vs rollback image vs restore

---

## 9) Configuration & Secrets Management

### 9.1 Environment variables

Rules:
- do not hardcode secrets
- separate per environment

### 9.2 Secret rotation

- rotate payment keys and JWT secrets
- document blast radius and rollback plan

### 9.3 CI/CD secrets

- store secrets in CI secret manager
- do not print secrets in logs

---

## 10) Logging, Audit & Traceability

### 10.1 Canonical log schema

Legacy spec:
- `/docs/ops/log_schema.md`

Key fields:
- `request_id`
- `tenant_id`

### 10.2 Audit coverage

Audit should include (at least):
- tenant created/disabled/deleted
- admin login failures
- policy changes
- break-glass actions

---

## 11) Password Reset & Break-Glass

See:
- `/docs/new/en/admin/password-reset.md`

---

## 12) Common Errors & Fixes

### 12.1 Admin login “Network Error”

Collect:
- request URL
- status code
- response body / console error

If request goes to wrong host/protocol → fix frontend baseURL.
If request goes to `/api/...` but fails → investigate proxy/backend.

### 12.2 Frozen lockfile failure

See:
- `/docs/new/en/runbooks/ci.md`

### 12.3 Migration issues

See:
- Section 8

---

## 13) Performance & Guardrails

See also:
- `/docs/new/en/api/overview.md`
- `/docs/new/en/api/payments.md`

### 13.1 Rate limits

The backend includes a simple in-memory rate limiter for critical endpoints.
Implementation:
- `backend/app/middleware/rate_limit.py`

Notes:
- dev/test environments relax limits
- prod/staging are stricter (e.g. login)

### 13.2 Background jobs

Document:
- scheduler used
- queue/worker infrastructure
- high-cost operations (e.g. purge)

---

## 14) Support & Incident Flow

### 14.1 Severity levels

- **P0:** full outage, money movement blocked, data integrity risk
- **P1:** major degradation, partial outage
- **P2:** non-critical bug affecting some users
- **P3:** minor issue / cosmetic

### 14.2 First places to look

- backend logs (correlate with `request_id`)
- audit log (who did what)
- database health and migrations

### 14.3 Rollback vs hotfix

- Rollback when risk is high and fix is unclear
- Hotfix when change is isolated and verified

Legacy reference:
- `/docs/ops/dr_runbook.md`
