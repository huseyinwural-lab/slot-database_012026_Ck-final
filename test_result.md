# Test Results - Sprint 1 & 2 (Payment/Wallet EPIC)

[NOTE]
This file is used by Emergent testing subagents to coordinate and record test runs.
Do not delete sections unless instructed.
[/NOTE]

## Latest iteration

### 2026-01-04 (Docs-only) — Documentation smoke checks
- Ran: `./scripts/docs_smoke.sh`
- Result: PASS
- Scope:

### 2026-01-05 (CI) — Frontend lint lockfile determinism
- Goal: Replicate CI `yarn install --frozen-lockfile` behavior locally and stabilize dependency graph.
- Environment:
  - Node: v20.19.6
  - Yarn: 1.22.22
- Actions:
  - Clean install: removed `frontend/node_modules`, ran `yarn cache clean --all`, then `yarn install`.
  - Verified: `yarn install --frozen-lockfile` passes locally.
  - Verified: `yarn lint` passes locally.
- Change prepared:
  - `frontend/yarn.lock` updated (lockfile drift fix) — expected to unblock `frontend-lint.yml` CI.
  - `.github/workflows/frontend-lint.yml` pins Node to `20.19.6` (to match canonical environment).

### 2026-01-05 (Testing Agent) — CI/lockfile drift validation
- **VALIDATION RESULTS:**
  1. ✅ `yarn install --frozen-lockfile` in frontend: PASS (Already up-to-date, completed in 0.28s)
  2. ✅ `yarn lint` in frontend: PASS (ESLint completed successfully in 0.83s)
  3. ✅ Git diff validation: Only `frontend/yarn.lock` modified (200 lines changed: 48 insertions, 152 deletions)
  4. ⚠️  Note: `.github/workflows/frontend-lint.yml` was NOT modified in current state (already contains Node 20.19.6 pinning)

- **CI Drift Analysis:**
  - **Root causes:** Node/Yarn version mismatches between local dev and CI environments, package registry resolution differences, cache inconsistencies
  - **Mitigation:** Node version pinning (20.19.6) in CI workflow, Yarn classic version pinning (1.22.22), frozen lockfile enforcement
  - **Current state:** Lockfile drift resolved, CI environment standardized


### 2026-01-05 (Docs) — Release Readiness Checklist added
- Added: `/docs/new/en/runbooks/release-readiness-checklist.md` and `/docs/new/tr/runbooks/release-readiness-checklist.md`
- Linked from: `docs/new/*/guides/ops-manual.md` and `docs/new/*/runbooks/README.md`
- Ran: `./scripts/docs_smoke.sh`
- Result: PASS

### 2026-01-05 (Docs) — Backend Gap Register triage hardening
- Updated: `/docs/new/en/runbooks/backend-gap-register.md` + `/docs/new/tr/runbooks/backend-gap-register.md`
- Added: Triage Summary table (Ops view), standard fields (Owner/SLA/Target Version), status flow (Open→In Progress→Fixed→Verified)
- Seeded top priorities: G-001 (Games Import 404), G-002 (API Keys toggle 404), G-003 (Reports/Simulator stub)
- Ran: `./scripts/docs_smoke.sh`
- Result: PASS


### 2026-01-05 (Docs) — Verification-driven contracts for top gaps
- Updated G-001/G-002/G-003 in backend gap register with explicit Verification contracts (endpoint + expected status/body + UI steps)
- Ran: `./scripts/docs_smoke.sh`
- Result: PASS

### 2026-01-05 (Backend) — G-001 Games Import endpoints implemented + tests
- Implemented endpoints (sync MVP):
  - POST /api/v1/game-import/manual/upload (multipart: file|bundle|upload)
  - GET  /api/v1/game-import/jobs/{job_id}
  - POST /api/v1/game-import/jobs/{job_id}/import
- Added SQLModel tables: game_import_job, game_import_item (job + items)
- Hardening: upload size limit (50MB), max items (10k), zip-slip path traversal guard
- Tenant isolation: enforced via tenant_id filter + owner impersonation handled by existing X-Tenant-ID resolver
- Audit events (best-effort): upload/import attempt + success/fail
- Tests: `pytest -q tests/test_game_import_endpoints.py` ✅



  - EN/TR parity
  - broken link scan
  - TODO/PLACEHOLDER ban
  - Admin manual quality gates:
    - min ≥8 error scenarios
    - keyword patterns (case-insensitive + minimal variations)
  - Docs: common errors guide (18 platform-wide error types)
  - Code: tenant creation permission hard-stop + audit requirements
  - Added/updated docs:
    - `/docs/new/en/runbooks/backend-gap-register.md` (+ migrated fields: First Seen / Environment / Status)
    - `/docs/new/tr/runbooks/backend-gap-register.md` (+ migrated fields: First Seen / Environment / Status)
    - Backend hardening:
      - Tenant creation restricted to platform owner (`is_platform_owner == true`) at backend endpoint (`POST /api/v1/tenants/`)
      - Audit events for tenant creation attempts and successes:
        - `tenant.create.attempt` (attempt + blocked + failed)
        - `tenant.created` (success)
      - Create payload forbids unknown fields (prevents `is_system`/system-tenant smuggling)

    - `/docs/new/en/admin/system/settings.md`
    - `/docs/new/tr/admin/system/settings.md`
    - `/docs/new/en/admin/system/cms.md`
    - `/docs/new/tr/admin/system/cms.md`
    - Risk & Compliance module pages:
      - `/docs/new/en/admin/risk-compliance/risk-rules.md`
      - `/docs/new/en/admin/risk-compliance/fraud-check.md`
      - `/docs/new/en/admin/risk-compliance/approval-queue.md`
      - `/docs/new/en/admin/risk-compliance/responsible-gaming.md`
      - `/docs/new/tr/admin/risk-compliance/risk-rules.md`
      - `/docs/new/tr/admin/risk-compliance/fraud-check.md`
      - `/docs/new/tr/admin/risk-compliance/approval-queue.md`
      - `/docs/new/tr/admin/risk-compliance/responsible-gaming.md`
    - Operations module pages:
      - `/docs/new/en/admin/operations/kyc-verification.md`
      - `/docs/new/en/admin/operations/crm-comms.md`
      - `/docs/new/en/admin/operations/bonuses.md`
      - `/docs/new/en/admin/operations/affiliates.md`
      - `/docs/new/en/admin/operations/support.md`
      - `/docs/new/tr/admin/operations/kyc-verification.md`
      - `/docs/new/tr/admin/operations/crm-comms.md`
      - `/docs/new/tr/admin/operations/bonuses.md`
      - `/docs/new/tr/admin/operations/affiliates.md`
      - `/docs/new/tr/admin/operations/support.md`
    - Game Engine module pages:
      - `/docs/new/en/admin/game-engine/robots.md`
      - `/docs/new/en/admin/game-engine/math-assets.md`
      - `/docs/new/tr/admin/game-engine/robots.md`
      - `/docs/new/tr/admin/game-engine/math-assets.md`
    - Guides:
      - `/docs/new/en/guides/common-errors.md`
      - `/docs/new/tr/guides/common-errors.md`

## Previous history

(legacy content retained below)
