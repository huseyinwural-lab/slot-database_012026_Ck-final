# Admin Panel Manual (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Platform Engineering  

This document is a **menu-driven, operations-grade** manual for the Admin Panel.
It is intended for admins to:
- understand what each menu does
- perform common procedures (game upload/import, report export, simulation)
- troubleshoot failures with a deterministic checklist

> Source of truth: EN. TR mirror: `/docs/new/tr/guides/admin-panel-manual.md`.

---

## Global troubleshooting rules (apply everywhere)

When something fails, always capture **3 facts** first:
1) The failing request URL (DevTools → Network)
2) Status code (0/401/403/404/409/429/500)
3) Response body / error message (1–2 lines)

Then:
- If it was a **write action** (toggle/approve/import/create/update): check **System → Audit Log** around the timestamp.
- If it was a **runtime error** (timeouts/500): check **System → Logs → Error Logs**.

Log search keys (most useful):
- `request_id` (if available)
- domain IDs: `player_id`, `tx_id`, `job_id`, `tenant_id`, `campaign_id`

---

## Permissions / visibility (why menus appear or not)

Menu items can be hidden by:
- owner-only / tenant-only restriction
- capability flags (feature gates)

Reference:
- `frontend/src/config/menu.js`
- `frontend/src/components/Layout.jsx`

---

# Core

## Dashboard

**Purpose**
Operational overview for key metrics and recent activity.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/dashboard/comprehensive-stats`

**Logs / Audit (where to look)**
- If widgets are empty: System → Logs → Error Logs
- If request returns 401: re-login; check Admin Users → Sessions

**Common errors & fixes**
- Blank widgets / missing data → verify tenant context and API availability.

---

## Players

**Purpose**
Search, inspect and manage player accounts.

**Sub-sections (screens / tabs)**
- Player List (`/players`)
- Player Detail (`/players/:id`) tabs:
  - Profile
  - KYC
  - Finance
  - Games
  - Logs
  - Notes

**Relevant API endpoints (as used by UI)**
- List/search:
  - `GET /api/v1/players`
- Player detail:
  - `GET /api/v1/players/{player_id}`
  - `PUT /api/v1/players/{player_id}`
- Player finance:
  - `GET /api/v1/players/{player_id}/transactions`
  - `POST /api/v1/players/{player_id}/balance` (balance adjustments)
- Player KYC:
  - `GET /api/v1/players/{player_id}/kyc`
  - `POST /api/v1/kyc/{doc_id}/review`
- Player logs:
  - `GET /api/v1/players/{player_id}/logs`

**Logs / Audit (where to look)**
- UI load failures: System → Logs → Error Logs
- Player edits/balance changes: System → Audit Log (filter by `actor_user_id`, `resource_type=player`, or `request_id`)

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Player page fails to load | API error / auth | Check failing request and login status |
| KYC tab empty | KYC disabled or no docs | Verify capabilities + player state |
| Balance change fails | permission / policy | Check Audit Log + response body |

---

## Finance (owner-only)

**Purpose**
Financial operations: transactions, reconciliation, chargebacks, reports.

**Sub-sections (tabs)**
- Transactions
- Reports
- Reconciliation
- Chargebacks

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/finance/transactions` (with query params)
- `GET /api/v1/finance/reports`

**Logs / Audit (where to look)**
- System → Logs → Error Logs (timeouts/500)
- System → Audit Log for manual actions that mutate state

**Common errors & fixes**
- 403 forbidden → you are not platform owner.

---

## Withdrawals (owner-only)

**Purpose**
Process and review withdrawal requests.

**Sub-sections (workflow actions)**
- List withdrawals
- Recheck
- Review (approve/reject)
- Payout
- Mark Paid

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/finance/withdrawals`
- `POST /api/v1/finance/withdrawals/{tx_id}/recheck`
- `POST /api/v1/finance/withdrawals/{tx_id}/review`
- `POST /api/v1/finance/withdrawals/{tx_id}/payout`
- `POST /api/v1/finance/withdrawals/{tx_id}/mark-paid`

**Logs / Audit (where to look)**
- Review/mark-paid/payout actions: System → Audit Log (filter by `tx_id`/time window)
- Provider/webhook related issues: System → Logs → Error Logs + Webhooks docs

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Payout action fails | provider state mismatch | Check payout status + webhook failures |
| "Network error" | proxy/baseURL issue | Verify request goes to `/api/...` |

---

## All Revenue (owner-only)

**Purpose**
Cross-tenant revenue analytics for platform owners.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/reports/revenue/all-tenants`

**Logs / Audit (where to look)**
- If missing/empty: confirm you are owner; check System → Logs → Error Logs

---

## My Revenue (tenant-only)

**Purpose**
Revenue analytics for the current tenant.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/reports/revenue/my-tenant`

---

## Games

**Purpose**
Manage the game catalog and import/upload new game bundles.

**Sub-sections (tabs)**
- Slots & Games
- Live Tables
- Upload & Import

### Slots & Games

**What it does**
- View catalog list
- Enable/disable games (toggle)

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/games`
- `POST /api/v1/games/{game_id}/toggle`

**Logs / Audit (where to look)**
- Toggle actions: System → Audit Log (resource_type=game)

### Live Tables

**What it does**
- Manage live table listings (provider-backed)

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/tables`
- `POST /api/v1/tables`

### Upload & Import (Game Import Wizard)

**What it does**
Upload and import a new game bundle via analyze → preview → import flow.

**Step-by-step: upload/import**
1) Games → Upload & Import
2) Choose import type:
   - Upload HTML5 Game Bundle
   - Upload Unity WebGL Bundle
3) Select client type (HTML5/Unity)
4) Pick a file (bundle)
5) Click **Upload & Analyze**
6) Review preview:
   - errors / warnings
7) If validation is clean, click **Import This Game**

**Relevant API endpoints (as used by UI)**
- Analyze/upload:
  - `POST /api/v1/game-import/manual/upload` (multipart)
- Preview:
  - `GET /api/v1/game-import/jobs/{job_id}`
- Finalize:
  - `POST /api/v1/game-import/jobs/{job_id}/import`

**Logs / Audit (where to look)**
- Import job failures: System → Logs → Error Logs (search by `job_id`)
- If imports mutate catalog: check Audit Log around import time

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Upload fails immediately | file too large / proxy limit | Reduce size or increase infra upload limit |
| Preview validation errors | invalid manifest/assets | Fix bundle structure and re-upload |
| Import disabled | validation errors present | Resolve errors first |

---

## VIP Games

**Purpose**
Mark games as VIP and manage VIP visibility/settings.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/games`
- `PUT /api/v1/games/{game_id}/details` (VIP tags/details)

**Logs / Audit (where to look)**
- Settings mutations: Audit Log (resource_type=game)

---

# Operations

## KYC Verification

**Purpose**
Review and verify player KYC documents.

**Sub-sections (tabs)**
- Dashboard
- Verification Queue
- Rules & Levels

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/kyc/dashboard`
- `GET /api/v1/kyc/queue`
- `POST /api/v1/kyc/documents/{doc_id}/review`

**Logs / Audit (where to look)**
- Document review actions: Audit Log (resource_type=kyc)

---

## CRM & Comms

**Purpose**
Create and send campaigns.

**Sub-sections (tabs)**
- Campaigns
- Templates
- Segments
- Channels

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/crm/campaigns`
- `GET /api/v1/crm/templates`
- `GET /api/v1/crm/segments`
- `GET /api/v1/crm/channels`
- `POST /api/v1/crm/campaigns`
- `POST /api/v1/crm/campaigns/{campaign_id}/send`

**Logs / Audit (where to look)**
- Campaign send failures: System → Logs → Error Logs
- Admin-triggered sends: Audit Log

---

## Bonuses

**Purpose**
Manage bonus campaigns.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/bonuses/campaigns`
- `POST /api/v1/bonuses/campaigns`
- `POST /api/v1/bonuses/campaigns/{id}/status`

---

## Affiliates

**Purpose**
Manage affiliate partners, offers, tracking, payouts and reports.

**Sub-sections (tabs)**
- Partners
- Offers
- Tracking
- Payouts
- Creatives
- Reports

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/affiliates`
- `GET /api/v1/affiliates/offers`
- `GET /api/v1/affiliates/links`
- `GET /api/v1/affiliates/payouts`
- `GET /api/v1/affiliates/creatives`
- `POST /api/v1/affiliates`
- `POST /api/v1/affiliates/offers`
- `POST /api/v1/affiliates/links`
- `POST /api/v1/affiliates/payouts`
- `POST /api/v1/affiliates/creatives`
- `PUT /api/v1/affiliates/{id}/status`

---

## Kill Switch (owner-only)

**Purpose**
Emergency stop for high-risk operations.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/tenants/` (tenant list)
- `POST /api/v1/kill-switch/tenant` (disable module per tenant)

**Logs / Audit (where to look)**
- Always check Audit Log after kill-switch changes.

---

## Support

**Purpose**
Ticketing and customer support tooling.

**Sub-sections (tabs)**
- Overview
- Inbox
- Live Chat
- Help Center
- Config

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/support/dashboard`
- `GET /api/v1/support/tickets`
- `GET /api/v1/support/chats`
- `GET /api/v1/support/kb`
- `GET /api/v1/support/canned`
- `POST /api/v1/support/tickets/{ticket_id}/message`
- `POST /api/v1/support/canned`

---

# Risk & Compliance

## Risk Rules (owner-only)

**Purpose**
Create and toggle risk rules; manage velocity, blacklist, cases and evidence.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/risk/dashboard`
- `GET /api/v1/risk/rules`
- `POST /api/v1/risk/rules`
- `POST /api/v1/risk/rules/{id}/toggle`
- `GET /api/v1/risk/velocity`
- `GET /api/v1/risk/blacklist`
- `POST /api/v1/risk/blacklist`
- `GET /api/v1/risk/cases`
- `PUT /api/v1/risk/cases/{case_id}/status`
- `GET /api/v1/risk/alerts`
- `GET /api/v1/risk/evidence`
- `POST /api/v1/risk/evidence`

**Logs / Audit (where to look)**
- Rule toggles and case updates: Audit Log

---

## Fraud Check (owner-only)

**Purpose**
Fraud analysis and case investigation.

**Relevant API endpoints (as used by UI)**
- `POST /api/v1/fraud/analyze`

---

## Approval Queue (owner-only)

**Purpose**
Handle approval workflows.

**Sub-sections (tabs)**
- Pending
- Approved
- Rejected
- Policies
- Delegations

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/approvals/requests?status=...`
- `GET /api/v1/approvals/rules`
- `GET /api/v1/approvals/delegations`
- `POST /api/v1/approvals/requests/{request_id}/action`

---

## Responsible Gaming (owner-only)

**Purpose**
Responsible Gaming controls and admin overrides.

**Relevant API endpoints (as used by UI)**
- `POST /api/v1/rg/admin/override/{player_id}`

---

# Game Engine

## Robots

**Purpose**
Manage game robots and operations like toggle/clone.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/robots`
- `POST /api/v1/robots/{robot_id}/toggle`
- `POST /api/v1/robots/{robot_id}/clone`

---

## Math Assets

**Purpose**
Manage math/model assets for games.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/math-assets`
- `POST /api/v1/math-assets`

---

# System

## CMS (owner-only)

**Purpose**
Manage content pages, banners, media, legal and system content.

**Sub-sections (tabs)**
- Overview
- Pages
- Homepage
- Banners
- Collections
- Popups
- Media
- i18n
- Legal
- A/B Test
- System
- Audit

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/cms/dashboard`
- `GET /api/v1/cms/pages`
- `POST /api/v1/cms/pages`
- `GET /api/v1/cms/banners`
- `GET /api/v1/cms/collections`
- `GET /api/v1/cms/popups`
- `GET /api/v1/cms/translations`
- `GET /api/v1/cms/media`
- `GET /api/v1/cms/legal`
- `GET /api/v1/cms/experiments`
- `GET /api/v1/cms/audit`

---

## Reports

**Purpose**
Generate and export platform reports.

**Sub-sections (sidebar groups in Reports)**
- Overview / Real-Time
- Financial / Players / Games / Providers
- Bonuses / Affiliates / CRM / CMS
- Risk & Fraud / Responsible Gaming / KYC
- Operational / Custom Builder / Scheduled
- Export Center

**Relevant API endpoints (as used by UI)**
- Data tabs:
  - `GET /api/v1/reports/overview`
  - `GET /api/v1/reports/financial`
  - `GET /api/v1/reports/players/ltv`
  - `GET /api/v1/reports/games`
  - `GET /api/v1/reports/providers`
  - `GET /api/v1/reports/bonuses`
  - `GET /api/v1/reports/affiliates`
  - `GET /api/v1/reports/risk`
  - `GET /api/v1/reports/rg`
  - `GET /api/v1/reports/kyc`
  - `GET /api/v1/reports/crm`
  - `GET /api/v1/reports/cms`
  - `GET /api/v1/reports/operational`
  - `GET /api/v1/reports/schedules`
  - `GET /api/v1/reports/exports`
- Export jobs:
  - `POST /api/v1/reports/exports`

**Logs / Audit (where to look)**
- Export fails: Logs → Error Logs
- If exports are async: verify worker/queue health in ops

---

## Logs (owner-only)

**Purpose**
System logs and troubleshooting.

**Sub-sections (sidebar groups in Logs)**
- System Events
- Cron Jobs
- Service Health
- Deployments
- Config Changes
- Error Logs
- Queue / Workers
- Database Logs
- Cache Logs
- Log Archive
- Trace View (placeholder)

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/logs/events`
- `GET /api/v1/logs/cron`
- `POST /api/v1/logs/cron/run`
- `GET /api/v1/logs/health`
- `GET /api/v1/logs/deployments`
- `GET /api/v1/logs/config`
- `GET /api/v1/logs/errors`
- `GET /api/v1/logs/queues`
- `GET /api/v1/logs/db`
- `GET /api/v1/logs/cache`
- `GET /api/v1/logs/archive`

---

## Audit Log (owner-only)

**Purpose**
Immutable record of administrative actions.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/audit/events` (filters: action/resource_type/status/actor/request_id)
- `GET /api/v1/audit/export` (CSV)

**Logs / Audit (where to look)**
- This page itself is the primary source for admin mutations.
- Use `request_id` filter to correlate multiple actions.

---

## Admin Users

**Purpose**
Admin identity governance (users, roles, teams, sessions, invites, security).

**Sub-sections (tabs)**
- Admin Users
- Roles
- Teams
- Activity Log
- Permission Matrix
- IP & Devices
- Login History
- Security
- Sessions
- Invites
- API Keys
- Risk Score
- Delegation

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/tenants/` (tenant list)
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `GET /api/v1/admin/roles`
- `GET /api/v1/admin/teams`
- `GET /api/v1/admin/sessions`
- `GET /api/v1/admin/invites`
- `GET /api/v1/admin/keys`
- `GET /api/v1/admin/security`
- `GET /api/v1/admin/activity-log?...`
- `GET /api/v1/admin/login-history?...`
- `GET /api/v1/admin/permission-matrix`
- `GET /api/v1/admin/ip-restrictions`
- `POST /api/v1/admin/ip-restrictions`
- `GET /api/v1/admin/device-restrictions`
- `PUT /api/v1/admin/device-restrictions/{device_id}/approve`

**Logs / Audit (where to look)**
- User create/invite/role change: Audit Log
- Login issues: Admin Users → Login History + System Logs → Error Logs

---

## Tenants (owner-only)

**Purpose**
Create/manage tenants.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/tenants/`
- `POST /api/v1/tenants/`
- `PATCH /api/v1/tenants/{tenant_id}`

**Logs / Audit (where to look)**
- All tenant mutations must appear in Audit Log.

---

## API Keys (owner-only)

**Purpose**
Manage platform API keys.

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/api-keys/`
- `GET /api/v1/api-keys/scopes`
- `POST /api/v1/api-keys/`
- `PATCH /api/v1/api-keys/{id}`

---

## Feature Flags (owner-only)

**Purpose**
Toggle feature flags and experiments.

**Sub-sections (tabs)**
- Feature Flags
- Experiments
- Segments
- Analytics
- Results
- Audit Log
- Env Compare
- Groups

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/flags/`
- `GET /api/v1/flags/experiments`
- `GET /api/v1/flags/segments`
- `GET /api/v1/flags/audit-log`
- `GET /api/v1/flags/environment-comparison`
- `GET /api/v1/flags/groups`
- `POST /api/v1/flags/{flag_id}/toggle`
- `POST /api/v1/flags/kill-switch`
- `POST /api/v1/flags/`
- `POST /api/v1/flags/experiments/{exp_id}/start`
- `POST /api/v1/flags/experiments/{exp_id}/pause`

**Logs / Audit (where to look)**
- Always verify Audit Log for flag toggles.

---

## Simulator

**Purpose**
Simulation Lab for scenarios, math/portfolio/bonus/risk modules.

**Sub-sections (tabs)**
- Overview
- Game Math
- Portfolio
- Bonus
- Cohort/LTV
- Risk
- RG
- A/B Sandbox
- Scenario Builder
- Archive

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/simulation-lab/runs`

**Logs / Audit (where to look)**
- If runs fail to load: System → Logs → Error Logs

---

## Settings (owner-only)

**Purpose**
Platform settings and policies.

**Sub-sections (tabs)**
- Brands
- Domains
- Currencies
- Payment Providers
- Payments Policy
- Countries
- Games
- Communication
- Regulatory
- Defaults
- API Keys
- Theme
- Maintenance
- Versions
- Audit

**Relevant API endpoints (as used by UI)**
- `GET /api/v1/settings/brands`
- `GET /api/v1/settings/currencies`
- `GET /api/v1/settings/country-rules`
- `GET /api/v1/settings/platform-defaults`
- `GET /api/v1/settings/api-keys`
- `GET /api/version`

**Logs / Audit (where to look)**
- If settings API returns 404: backend route mismatch; check backend routes and proxy.
