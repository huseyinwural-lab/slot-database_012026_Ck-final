# Admin Panel Manual (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Platform Engineering  

This document is a **menu-driven, operations-grade** manual for the Admin Panel.
It is intended for admins to:
- understand what each menu does
- perform common procedures (game upload, report export, simulation)
- troubleshoot failures with a deterministic checklist

> Source of truth: EN. TR mirror: `/docs/new/tr/guides/admin-panel-manual.md`.

---

## How this manual is structured

For each menu item:
1) Purpose (what it is for)
2) Sub-sections (tabs / sub-pages)
3) Common procedures (step-by-step)
4) Common errors & fixes
5) Permissions/visibility notes

---

# Core

## Dashboard

**Purpose**
Operational overview for key metrics and recent activity.

**Common procedures**
- Validate that the current tenant context is correct (tenant switcher).

**Common errors & fixes**
- Blank widgets / missing data → verify tenant context and API availability.

---

## Players

**Purpose**
Search, inspect and manage player accounts.

**Key screens / sub-sections**
- Player List (`/players`)
- Player Detail (`/players/:id`) tabs:
  - Profile
  - KYC
  - Finance
  - Games
  - Logs
  - Notes

**Common procedures**
1) Find a player
- Use Players list filters/search.
- If needed, use Global Search (Ctrl+K) from the top bar.

2) Review KYC for a player
- Open Player Detail → KYC tab.

3) Adjust player balance (if enabled)
- Player Detail → Finance tab (actions depend on permissions).

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Player page fails to load | API error / auth | Check network request to `/api/v1/players/{id}` and login status |
| KYC tab empty | KYC feature disabled or no docs | Verify feature flags/capabilities and player KYC state |

---

## Finance (owner-only)

**Purpose**
Financial operations: transactions, reconciliation, chargebacks, reports.

**Sub-sections (tabs)**
- Transactions
- Reports
- Reconciliation
- Chargebacks

**Common procedures**
- Investigate a transaction: Finance → Transactions → search by ID/player.

**Common errors & fixes**
- 403 forbidden → you are not platform owner (owner-only menu).

---

## Withdrawals (owner-only)

**Purpose**
Process and review withdrawal requests.

**Implementation note**
In this UI the withdrawals workflow is implemented in `FinanceWithdrawals.jsx` and includes actions like:
- payout
- recheck
- review
- mark paid

**Common procedures (high level)**
1) Open Withdrawals
2) Filter pending withdrawals
3) For a tx:
- Recheck (refresh provider/state)
- Review (approve/reject)
- Payout (trigger payout)
- Mark Paid (finalize)

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Payout action fails | provider/webhook state mismatch | Check backend logs + payout status; verify webhooks |
| "Network error" in UI | proxy/baseURL issue | Verify request goes to `/api/...` and not wrong host |

---

## All Revenue (owner-only)

**Purpose**
Cross-tenant revenue analytics for platform owners.

**Common errors & fixes**
- Missing tenant list/data → verify you are owner and tenants exist.

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

**Common procedures**
- Enable/disable a game:
  1) Games → Slots & Games
  2) Find the game row
  3) Toggle status (calls `/api/v1/games/{gameId}/toggle`)

**Common errors & fixes**
- Toggle fails → check API response for permission/validation errors.

### Live Tables

**What it does**
- Manage live table listings (provider-backed)

**Common errors & fixes**
- Empty list → provider integration not configured or tenant policy missing.

### Upload & Import (Game Import Wizard)

**What it does**
Upload and import a new game bundle (HTML5 / Unity WebGL) via an analyze → preview → import flow.

**Step-by-step: upload/import**
1) Games → Upload & Import
2) Choose import type:
   - Upload HTML5 Game Bundle
   - Upload Unity WebGL Bundle
3) Select client type (HTML5/Unity)
4) Pick a file (bundle)
5) Click **Upload & Analyze**
6) Review "Manual Import Preview" results:
   - errors / warnings
7) If validation is clean, click **Import This Game**

**What happens under the hood (ops useful)**
- Analyze creates a job and preview items
- Import finalizes the job

API calls used by the page:
- `GET /api/v1/game-import/jobs/{job_id}` (preview)
- `POST /api/v1/game-import/jobs/{job_id}/import` (finalize)

**Common errors & fixes**
| Symptom | Likely cause | Fix |
|---|---|---|
| Upload fails immediately | file too large / proxy limit | Use smaller bundle or adjust infra upload limits |
| Preview shows validation errors | invalid manifest/assets | Fix bundle structure and re-upload |
| Import button disabled | validation errors present | Resolve errors first; import is blocked |

---

## VIP Games

**Purpose**
Mark games as VIP and manage VIP visibility/settings.

**Common errors & fixes**
- Save fails → missing permissions or invalid game id.

---

# Operations

## KYC Verification

**Purpose**
Review and verify player KYC documents.

**Sub-sections (tabs)**
- Dashboard
- Verification Queue
- Rules & Levels

**Common procedures**
- Verify a document:
  1) KYC Verification → Verification Queue
  2) Open a document
  3) Approve/Reject (calls `/api/v1/kyc/.../review`)

**Common errors & fixes**
- 403 forbidden → feature disabled (`can_manage_kyc`) or role lacks permission.

---

## CRM & Comms

**Purpose**
Create and send campaigns.

**Sub-sections (tabs)**
- Campaigns
- Templates
- Segments
- Channels

**Common procedures**
- Send campaign:
  - CRM → Campaigns → Send (calls `/api/v1/crm/campaigns/{id}/send`)

---

## Bonuses

**Purpose**
Manage bonus campaigns.

**Common errors & fixes**
- Campaign status change fails → check API response; ensure tenant policy supports bonuses.

---

## Affiliates

**Purpose**
Manage affiliate partners, offers and payouts.

**Sub-sections (tabs)**
- Partners
- Offers
- Tracking
- Payouts
- Creatives
- Reports

---

## Kill Switch (owner-only)

**Purpose**
Emergency stop for high-risk operations.

**Common errors & fixes**
- Not visible → owner-only + `can_use_kill_switch` feature must be enabled.

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

---

# Risk & Compliance

## Risk Rules (owner-only)

**Purpose**
Create and toggle risk rules.

**Common procedures**
- Toggle a rule: calls `/api/v1/risk/rules/{id}/toggle`.

---

## Fraud Check (owner-only)

**Purpose**
Fraud analysis and case investigation.

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

---

## Responsible Gaming (owner-only)

**Purpose**
Responsible Gaming controls and admin overrides.

---

# Game Engine

## Robots

**Purpose**
Manage game robots (automation/testing) and toggle/clone them.

---

## Math Assets

**Purpose**
Manage math/model assets for games.

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

---

## Reports

**Purpose**
Generate and export platform reports.

**Sub-sections (tabs)**
- Export Center
- (other report groups: financial, players, games, providers, bonuses, affiliates, crm, cms, scheduled)

**Common procedures: export a report**
1) System → Reports
2) Open **Export Center**
3) Choose export type
4) Request export (calls `POST /api/v1/reports/exports`)

**Common errors & fixes**
- Export job not appearing → refresh; check backend worker/job processing if applicable.

---

## Logs (owner-only)

**Purpose**
System logs and troubleshooting.

---

## Audit Log (owner-only)

**Purpose**
View audited changes.

**Sub-sections (tabs)**
- Changes (Diff)
- Before/After
- Metadata & Context
- Raw JSON

---

## Admin Users

**Purpose**
Admin identity governance (users, roles, sessions, invites, security).

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

**Common procedures: invite admin**
1) Admin Users → Invites
2) Create invite
3) Copy invite link

---

## Tenants (owner-only)

**Purpose**
Create/manage tenants.

**Common procedures**
- Edit tenant feature flags/settings (calls `PATCH /api/v1/tenants/{id}`)

---

## API Keys (owner-only)

**Purpose**
Manage platform API keys.

---

## Feature Flags (owner-only)

**Purpose**
Toggle features and experiments.

**Sub-sections (tabs)**
- Feature Flags
- Experiments
- Segments
- Analytics
- Results
- Audit Log
- Env Compare
- Groups

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

**Common procedures: run a simulation**
1) System → Simulator
2) Choose a module tab (e.g. Risk)
3) Configure parameters
4) Run (if available)
5) Review runs under Archive

**Common errors & fixes**
- Runs list empty → no data yet or API `/api/v1/simulation-lab/runs` failing.

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

---

## Permissions & visibility rules (how menus appear)

Menu items can be hidden by:
- owner-only / tenant-only restriction
- feature capability flags
- menu flags from backend capabilities

Reference:
- `frontend/src/config/menu.js`
- `frontend/src/components/Layout.jsx`
