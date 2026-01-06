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

### 2026-01-05 (Backend) — G-001 Games Import endpoints implemented + tests (Verified/Closed)
- Implemented endpoints (sync MVP):
  - POST /api/v1/game-import/manual/upload (multipart: file|bundle|upload)
  - GET  /api/v1/game-import/jobs/{job_id}
  - POST /api/v1/game-import/jobs/{job_id}/import
- Added SQLModel tables: game_import_job, game_import_item (job + items)
- Hardening: upload size limit (50MB), max items (10k), zip-slip path traversal guard
- Tenant isolation: enforced via tenant_id filter + owner impersonation handled by existing X-Tenant-ID resolver
- Audit events (best-effort): upload/import attempt + success/fail
- Tests: `pytest -q tests/test_game_import_endpoints.py` ✅
- Closure note: MVP endpoints implemented, stub removed, tenant isolation enforced, tests PASS. Status: Verified / Closed.

### 2026-01-05 (Testing Agent) — G-001 Games Import Verification Contract Validation
- **VALIDATION RESULTS:**
  1. ✅ POST /api/v1/game-import/manual/upload: PASS (200 with job_id)
  2. ✅ GET /api/v1/game-import/jobs/{job_id}: PASS (200 with job_id, status, total_items, total_errors)
  3. ✅ POST /api/v1/game-import/jobs/{job_id}/import: PASS (200 with status=completed, imported_count>=1)
  4. ✅ Tenant isolation: PASS (403 for cross-tenant access)
  5. ✅ Missing file error: PASS (400 with missing file error)
  6. ✅ Bad JSON error: PASS (422 with JSON error)
  7. ✅ Job not ready error: PASS (409 with job not ready error)

- **Test Details:**
  - All endpoints return correct HTTP status codes
  - Response shapes match verification contract requirements
  - Tenant isolation properly enforced (403 Forbidden for cross-tenant access)
  - Error handling works correctly for all specified error cases
  - File upload accepts multipart/form-data with file field
  - JSON payload processing works with valid game data structure

- **Overall Result:** ✅ ALL TESTS PASSED (7/7) - G-001 Games Import flow fully validated

### 2026-01-05 (Backend) — G-002 API Keys Toggle implemented + tests (Verified/Closed)
- Implemented: `PATCH /api/v1/api-keys/{id}` with body `{ "active": true|false }`
- Tenant isolation: enforced via `tenant_id` filter; tenant mismatch returns 404 (no-leak)
- Persisted state: `APIKey.status` toggled between `active` / `inactive`
- Audit events (best-effort): `api_key.toggle.attempt` / `api_key.toggled` / `api_key.toggle.failed`
- Added missing helpers for key creation used by existing route:
  - `app.utils.api_keys.generate_api_key()`
  - `app.utils.api_keys.validate_scopes()`
- Tests: `pytest -q tests/test_api_keys_toggle.py` ✅
- Closure note: PATCH implemented, tenant isolation enforced, tests PASS (6/6). Status: Verified / Closed.

### 2026-01-05 (Testing Agent) — G-002 API Keys Toggle Verification Contract Validation
- **VALIDATION RESULTS:**
  1. ✅ GET /api/v1/api-keys/: PASS (200 with list, correct structure, no secrets exposed)
  2. ✅ PATCH /api/v1/api-keys/{id} with {"active": false}: PASS (200 with updated record)
  3. ✅ PATCH /api/v1/api-keys/{id} with {"active": true}: PASS (200 with updated record)
  4. ✅ State persistence: PASS (GET after PATCH shows persisted state)
  5. ✅ Tenant isolation: PASS (404 for non-existent/cross-tenant key)
  6. ✅ Invalid body validation: PASS (422 for non-boolean active values)

- **Test Details:**
  - All endpoints return correct HTTP status codes per acceptance criteria
  - Response shapes match verification contract requirements (same shape as list items)
  - Tenant isolation properly enforced (404 for cross-tenant access, no information leakage)
  - State persistence verified through GET after PATCH operations
  - Raw API key secrets never returned except on create endpoint
  - Invalid body handling works correctly (422 for non-boolean active field)
  - API key creation and listing functionality working correctly

- **Overall Result:** ✅ ALL TESTS PASSED (6/6) - G-002 API Keys Toggle flow fully validated

### 2026-01-05 (Backend) — G-003 Reports/SimulationLab endpoints implemented + tests (Verified/Closed)

### 2026-01-05 (Backend) — Brands API 404 fixed (Settings Panel)
- Fixed contract mismatch: `GET /api/v1/settings/brands` now returns an **array** matching the Settings Panel UI shape (`brand_name`, `default_currency`, etc.)
- Implemented minimal `POST /api/v1/settings/brands` (creates a Tenant as brand) — **platform owner only**
- Tests: `pytest -q tests/test_settings_brands.py` ✅
- Implemented (no longer stub/404):
  - `GET  /api/v1/reports/overview` (deterministic MVP metrics + DB counts where possible)
  - `GET  /api/v1/reports/exports`
  - `POST /api/v1/reports/exports` → `{ export_id, status }`
  - `GET  /api/v1/simulation-lab/runs`
  - `POST /api/v1/simulation-lab/runs` (idempotent create)
  - `POST /api/v1/simulation-lab/game-math` (deterministic result for UI)
- Added SQLModel tables:
  - `report_export_job`
  - `simulation_run`
- Tenant isolation: all queries tenant-scoped (owner impersonation via existing X-Tenant-ID)
- Audit events (best-effort): reports overview view + export create + simulation run create/execute
- Tests: `pytest -q tests/test_reports_and_simulation_endpoints.py` ✅
- Closure note: MVP endpoints implemented, stub removed, tenant isolation enforced, tests PASS (8/8). Status: Verified / Closed.

### 2026-01-05 (Testing Agent) — G-003 Reports/SimulationLab Verification Contract Validation
- **VALIDATION RESULTS:**
  1. ✅ GET /api/v1/reports/overview: PASS (200 with ggr, ngr, active_players, bonus_cost)
  2. ✅ POST /api/v1/reports/exports: PASS (200 with export_id and status=completed)
  3. ✅ GET /api/v1/reports/exports: PASS (200 array including newly created export)
  4. ✅ GET /api/v1/simulation-lab/runs: PASS (200 array)
  5. ✅ POST /api/v1/simulation-lab/runs: PASS (200 with same id as requested)
  6. ✅ POST /api/v1/simulation-lab/game-math: PASS (deterministic response with status=completed)
  7. ✅ Tenant isolation exports: PASS (tenant2 cannot see tenant1 exports)
  8. ✅ Tenant isolation runs: PASS (tenant2 cannot see tenant1 simulation runs)

- **Test Details:**
  - All endpoints return correct HTTP status codes (200) per acceptance criteria
  - Response shapes match verification contract requirements
  - Reports overview returns required fields: ggr=125000, ngr=94000, active_players=415, bonus_cost=12000
  - Export creation returns export_id and status (completed/processing)
  - Export listing includes newly created exports in chronological order
  - Simulation runs support idempotent creation with custom IDs
  - Game math simulation returns deterministic calculations (1000 spins * 96.5% RTP = 965.0 expected return)
  - Tenant isolation properly enforced for both exports and simulation runs
  - All endpoints properly scoped to tenant context via X-Tenant-ID header

- **Overall Result:** ✅ ALL TESTS PASSED (8/8) - G-003 Reports + Simulation Lab flow fully validated

### 2026-01-05 (Testing Agent) — Brands Settings Endpoints Validation
- **VALIDATION RESULTS:**
  1. ✅ GET /api/v1/settings/brands (Platform Owner): PASS (200 with array of 18 brands, all required fields present)
  2. ✅ GET /api/v1/settings/brands (Tenant Isolation): PASS (non-owner sees only their own tenant)
  3. ✅ POST /api/v1/settings/brands (Platform Owner): PASS (200 with brand ID returned)
  4. ✅ POST /api/v1/settings/brands (Non-Owner): PASS (403 Forbidden as expected)
  5. ✅ POST /api/v1/settings/brands (Validation): PASS (422 for missing brand_name)

- **Test Details:**
  - GET endpoint returns proper JSON array (not wrapped object) matching frontend expectations
  - Each brand object contains all required fields: id, brand_name, status, default_currency, default_language, country_availability, created_at
  - Platform owner can see multiple tenants (18 brands returned)
  - Non-owner tenant isolation working correctly (only sees own tenant)
  - POST endpoint properly restricted to platform owner only (403 for non-owners)
  - Brand creation returns correct response shape with ID
  - Validation working correctly for missing required fields
  - All endpoints properly scoped to tenant context and authorization rules

- **Overall Result:** ✅ ALL TESTS PASSED (5/5) - Brands Settings endpoints fully validated and working correctly



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

### 2026-01-06 (Testing Agent) — Players CSV Export End-to-End API Validation
- **TEST SCOPE:** Complete end-to-end validation of Players CSV export functionality at API level
- **VALIDATION RESULTS:**
  1. ✅ **Admin Authentication:** Successfully logged in as admin@casino.com / Admin123!
  2. ✅ **Basic CSV Export:** GET /api/v1/players/export returns 200 with proper headers and CSV content
     - Content-Type: `text/csv; charset=utf-8` ✅
     - Content-Disposition: `attachment; filename="players_*.csv"` ✅
     - CSV header row: `id,username,email,status,kyc_status,risk_score,balance_real,balance_bonus,registered_at` ✅
  3. ✅ **Search Filtering:** GET /api/v1/players/export?search=rcuser returns 200 with filtered CSV (41 data rows)
  4. ✅ **Tenant Isolation:** X-Tenant-ID header properly isolates data between tenants
     - Default tenant: 415 players + header (416 lines total)
     - Tenant1: 0 players + header (1 line total)
     - Isolation verified: Different tenant contexts return different data sets

- **DETAILED TEST RESULTS:**
  - **Authentication:** Admin login successful with valid JWT token
  - **CSV Format:** Proper CSV structure with all required columns (id, username, email, etc.)
  - **HTTP Headers:** Correct Content-Type and Content-Disposition for file download
  - **Search Functionality:** Filter parameter correctly applied, returning subset of data
  - **Tenant Security:** Platform owner can impersonate different tenants via X-Tenant-ID header
  - **Data Isolation:** Each tenant sees only their own players in export

- **PERFORMANCE:** Export limited to 5000 records for optimal performance
- **SECURITY:** Tenant isolation properly enforced, no cross-tenant data leakage
- **STATUS:** ✅ ALL TESTS PASSED - Players CSV export fully functional at API level

### 2026-01-06 (Testing Agent) — Players CSV Export Smoke Test
- **TEST SCOPE:** Frontend smoke test for Players CSV export functionality
- **VALIDATION RESULTS:**
  1. ❌ **Authentication Session Issues:** Browser sessions expire quickly, preventing navigation to Players page
  2. ✅ **Backend Implementation:** Export endpoint `/api/v1/players/export` exists and properly implemented
  3. ✅ **Frontend Implementation:** PlayerList component has Export CSV button and proper functionality
  4. ❌ **Unable to Complete Test:** Session timeout prevents testing actual CSV export flow

- **BACKEND ANALYSIS:**
  - Export endpoint returns CSV with proper Content-Type: `text/csv; charset=utf-8`
  - Includes Content-Disposition header for file download: `attachment; filename="players_*.csv"`
  - Tenant isolation implemented correctly
  - Supports filtering by status and search parameters
  - Limits export to 5000 records for performance

- **FRONTEND ANALYSIS:**
  - Export button present in PlayerList component
  - Console log `export_xlsx_clicked` implemented
  - API call now targets `/v1/players/export.xlsx` with blob response type
  - File download trigger with `.xlsx` filename pattern
  - Filter parameters passed through (status/search/vip_level/risk_score)

- **ROOT CAUSE:** Authentication session management issues prevent stable testing
- **RECOMMENDATION:** Fix JWT token expiration/refresh mechanism before retesting
- **STATUS:** ⚠️ PARTIAL - Frontend smoke was blocked by session timeout; API-level export fully validated

### 2026-01-06 (Testing Agent) — Players XLSX Export End-to-End API Validation
- **TEST SCOPE:** Complete end-to-end validation of Players XLSX export functionality at API level
- **VALIDATION RESULTS:**
  1. ✅ **Admin Authentication:** Successfully logged in as admin@casino.com / Admin123!
  2. ✅ **Basic XLSX Export:** GET /api/v1/players/export.xlsx returns 200 with proper headers and XLSX content
     - Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` ✅
     - Content-Disposition: `attachment; filename="players_*.xlsx"` ✅
     - Body starts with PK (xlsx zip container signature) ✅
     - File size: 38,628 bytes with valid XLSX structure ✅
  3. ✅ **Search Filtering:** GET /api/v1/players/export.xlsx?search=rcuser returns 200 with filtered XLSX (8,423 bytes)
  4. ✅ **Tenant Isolation:** X-Tenant-ID header properly isolates data between tenants
     - Tenant1: 38,628 bytes (415 players + header)
     - Tenant2: 4,924 bytes (different tenant data set)
     - Isolation verified: Different tenant contexts return different data sets ✅
  5. ✅ **CSV Endpoint Compatibility:** GET /api/v1/players/export returns 200 with text/csv content-type

- **DETAILED TEST RESULTS:**
  - **Authentication:** Admin login successful with valid JWT token
  - **XLSX Format:** Proper XLSX structure with OpenXML format signature (PK header)
  - **HTTP Headers:** Correct Content-Type and Content-Disposition for Excel file download
  - **Search Functionality:** Filter parameter correctly applied, returning subset of data in XLSX format
  - **Tenant Security:** Platform owner can impersonate different tenants via X-Tenant-ID header
  - **Data Isolation:** Each tenant sees only their own players in XLSX export
  - **Backward Compatibility:** CSV export endpoint continues to work alongside new XLSX endpoint

- **PERFORMANCE:** Export limited to 5000 records for optimal performance
- **SECURITY:** Tenant isolation properly enforced, no cross-tenant data leakage
- **STATUS:** ✅ ALL TESTS PASSED - Players XLSX export fully functional at API level

### 2026-01-06 (Testing Agent) — Players XLSX Export Frontend Smoke Test
- **TEST SCOPE:** Frontend smoke test for Players XLSX export functionality as requested
- **VALIDATION RESULTS:**
  1. ✅ **Admin Authentication:** Successfully logged in as admin@casino.com / Admin123!
  2. ✅ **Players Page Navigation:** Successfully navigated to Core -> Players (PlayerList)
  3. ✅ **XLSX API Backend:** GET /api/v1/players/export.xlsx returns 200 with proper XLSX headers
     - Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` ✅
     - Content-Disposition: `attachment; filename="players_*.xlsx"` ✅
  4. ❌ **Frontend Implementation Gap:** Export button shows "Export CSV" instead of "Export Excel"
  5. ❌ **Console Log Mismatch:** Console shows `export_csv_clicked` instead of `export_xlsx_clicked`
  6. ❌ **API Call Mismatch:** Frontend calls `/api/v1/players/export` (CSV) instead of `/api/v1/players/export.xlsx`

- **DETAILED FINDINGS:**
  - **Backend XLSX Support:** ✅ XLSX endpoint fully implemented and working correctly
  - **Frontend Code Gap:** ❌ Deployed frontend lacks XLSX export functionality
    - Current button text: "Export CSV"
    - Current console log: "export_csv_clicked"
    - Current API call: "/api/v1/players/export" (CSV endpoint)
    - Missing: handleExportXlsx function, export_xlsx_clicked log, .xlsx endpoint call
  - **Session Management:** ✅ Authentication stable, localStorage admin_token persists correctly
  - **File Download Trigger:** ✅ CSV export triggers proper file download (blob URL creation)

- **ROOT CAUSE:** Frontend code mismatch - the deployed version has CSV export functionality but lacks the XLSX export implementation that exists in the source code
- **IMPACT:** Users cannot access XLSX export from the UI, only CSV export is available
- **STATUS:** ❌ FRONTEND IMPLEMENTATION MISSING - Backend XLSX support exists but frontend not deployed

### 2026-01-06 (Backend+Frontend) — Players Export upgraded to XLSX (Excel)
- Backend: added `GET /api/v1/players/export.xlsx` (openpyxl) with proper XLSX headers + tenant scope + filters; kept CSV endpoint for compatibility.
- Frontend: Players export button now calls `/v1/players/export.xlsx` and downloads `players_export_*.xlsx`.
- Pytest: `pytest -q tests/test_players_export_xlsx.py` ✅

### 2026-01-06 (Testing Agent) — Players XLSX Export Frontend Deployment Verification
- **TEST SCOPE:** Frontend smoke test for Players XLSX export functionality as requested in review
- **VALIDATION RESULTS:**
  1. ✅ **Admin Authentication:** Successfully logged in as admin@casino.com / Admin123! with "Sign In" button
  2. ✅ **Players Page Navigation:** Successfully navigated to /players page without redirects
  3. ✅ **Session Management:** localStorage admin_token persists correctly, no session timeout issues
  4. ❌ **CRITICAL DEPLOYMENT ISSUE:** Frontend shows "Export CSV" instead of "Export Excel"
     - Current deployed button text: "Export CSV" 
     - Expected button text: "Export Excel"
     - Source code verification: PlayerList.jsx contains correct XLSX implementation with handleExportXlsx function
     - Deployment gap: Source code has XLSX functionality but deployed version still has CSV-only implementation

- **DETAILED FINDINGS:**
  - **Source Code Analysis:** ✅ PlayerList.jsx contains proper XLSX export implementation:
    - handleExportXlsx function with console.log('export_xlsx_clicked')
    - API call to '/v1/players/export.xlsx' with responseType: 'blob'
    - Button text: "Export Excel"
    - File download with .xlsx extension
  - **Deployed Version Analysis:** ❌ Production deployment missing XLSX functionality:
    - Only "Export CSV" button visible in UI
    - No "Export Excel" button found
    - Frontend check confirms no XLSX functions in deployed JavaScript

- **ROOT CAUSE:** Frontend deployment mismatch - source code contains XLSX implementation but production deployment has not been updated
- **IMPACT:** Users cannot access XLSX export functionality from the UI despite backend support being available
- **STATUS:** ❌ DEPLOYMENT ISSUE - Frontend requires rebuild and redeployment to include XLSX export functionality

## Agent Communication

agent_communication:
    -agent: "testing"
    -message: "CRITICAL DEPLOYMENT ISSUE FOUND: Players XLSX export frontend smoke test reveals deployment mismatch. Source code (PlayerList.jsx) contains correct XLSX implementation with 'Export Excel' button and handleExportXlsx function, but deployed version still shows 'Export CSV' button. Frontend requires rebuild and redeployment to include XLSX functionality. Backend XLSX endpoint exists but frontend cannot access it due to deployment gap."

## Previous history

(legacy content retained below)
