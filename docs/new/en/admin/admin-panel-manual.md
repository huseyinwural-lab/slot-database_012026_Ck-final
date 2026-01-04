# Admin Panel Manual (EN) — Hub

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Platform Engineering  

This is the **hub** for the Admin Panel manual.

- **Scope:** Navigation + where to find each menu’s procedures.
- **Source of truth:** EN. TR is a mirrored derivative.
- **Rule:** Detailed operating procedures live in the **menu pages** (linked below). Runbooks (break-glass, password reset) live under `/docs/new/en/runbooks/`.

---

## 0) How to use this manual

1) Find the menu you’re working on in the tree below.
2) Open the corresponding menu page.
3) For every incident/action, capture:
   - failing request URL + status code (DevTools → Network)
   - `x-request-id` response header (if present)
4) Validate outcome using the page’s **Verification (UI + Logs + Audit + DB)** section.

---

## 1) Critical security notes (read before production operations)

### 1.1 Tenant context and impersonation
- Platform Owner (Super Admin) can impersonate a tenant via `X-Tenant-ID` header.
- Tenant admins must **never** be able to override tenant context.
- Always verify you are operating on the intended tenant before destructive actions.

### 1.2 API keys
- API keys are production-grade secrets.
- Key secrets should only be shown once at creation time.
- If a key leak is suspected: revoke immediately, rotate, and produce audit evidence.

### 1.3 Kill Switch and blast radius
- Kill switch is a **high blast-radius** control.
- Always record: who toggled, why, which tenant/module, and rollback plan.

### 1.4 Break-glass
- Break-glass is a controlled exception process.
- Requires explicit approval and post-mortem.
- Use the runbook:
  - `/docs/new/en/runbooks/break-glass.md`

---

## 2) Menu tree → pages

> Source of truth for menu structure: `frontend/src/config/menu.js`

### Core
- Dashboard → `./core/dashboard.md`
- Players → `./core/players.md`
- Finance (owner-only) → `./core/finance.md`
- Withdrawals (owner-only) → `./core/withdrawals.md`
- All Revenue (owner-only) → `./core/all-revenue.md`
- Games → `./core/games.md`
- VIP Games → `./core/vip-games.md`

### Operations
- KYC Verification → `./operations/kyc-verification.md`
- CRM & Comms → `./operations/crm-comms.md`
- Bonuses → `./operations/bonuses.md`
- Affiliates → `./operations/affiliates.md`
- Kill Switch (owner-only) → `./operations/kill-switch.md`
- Support → `./operations/support.md`

### Risk & Compliance
- Risk Rules (owner-only) → `./risk-compliance/risk-rules.md`
- Fraud Check (owner-only) → `./risk-compliance/fraud-check.md`
- Approval Queue (owner-only) → `./risk-compliance/approval-queue.md`
- Responsible Gaming (owner-only) → `./risk-compliance/responsible-gaming.md`

### Game Engine
- Robots → `./game-engine/robots.md`
- Math Assets → `./game-engine/math-assets.md`

### System
- CMS (owner-only) → `./system/cms.md`
- Reports → `./system/reports.md`
- Logs (owner-only) → `./system/logs.md`
- Audit Log (owner-only) → `./system/audit-log.md`
- Admin Users → `./system/admin-users.md`
- Tenants (owner-only) → `./system/tenants.md`
- API Keys (owner-only) → `./system/api-keys.md`
- Feature Flags (owner-only) → `./system/feature-flags.md`
- Simulator → `./system/simulator.md`
- Settings (owner-only) → `./system/settings.md`

---

## 3) Global verification locations (applies to all menus)

### 3.1 UI verification
- System → Audit Log (mutations: create/update/approve/toggle/import)
- System → Logs (runtime errors/timeouts)

### 3.2 Application / container logs
- Backend (container logs): search by `request_id`, `tenant_id`, or domain IDs (`player_id`, `tx_id`, `job_id`).

### 3.3 Database audit tables (if present)
- Canonical audit table: `auditevent`
- Supporting tables may exist depending on deployment (e.g., login history, admin sessions).

---

## 4) Related runbooks

- Password reset: `/docs/new/en/runbooks/password-reset.md`
- Break-glass: `/docs/new/en/runbooks/break-glass.md`
- Common errors: `/docs/new/en/guides/common-errors.md`
