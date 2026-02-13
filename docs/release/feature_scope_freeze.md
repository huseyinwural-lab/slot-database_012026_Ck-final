# Feature Scope Freeze & Readiness Report

**Status:** PRE-LAUNCH CLEANUP
**Date:** 2026-02-16

## 1. Feature Scope (Release v1.0)

### ✅ Active (Included)
- **Authentication:** Admin Login, Player Login (JWT).
- **Wallet:** Deposit/Withdrawal, Balance Tracking, Ledger.
- **Game Engine:** Simulator, Pragmatic Play (Ready for Integ), Evolution (Ready for Integ).
- **Risk Management:** Rules, Blacklist, History (V2).
- **Reporting:** GGR, NGR, Daily Aggregates.
- **Back Office:** User Management, Approvals, Settings.

### 🚫 Disabled / Out of Scope (Code Present but Hidden)
- **Live Table Management:** `GameManagement.jsx` (TODO identified).
- **Robot Orchestrator:** `routes/robot.py` (Refactor pending).
- **CRM / Bonus Campaigns:** Stubs implemented, full UI hidden/disabled.
- **Affiliate System:** Models exist, UI pending.

### 🚧 Coming Soon (Placeholder UI)
- **Advanced Fraud AI:** Mocked via `/v1/fraud/analyze`.
- **Payment Intelligence:** Placeholder in Risk Dashboard.
- **Device Fingerprinting:** Placeholder in Risk Dashboard.

## 2. Technical Debt & TODOs (Post-Launch)
- **Auth:** Email sending is mocked (SendGrid TODO).
- **Robots:** SQL session refactor needed.
- **Frontend:** `handleToggleTable` in Game Management.

## 3. Cleanup Actions Taken
- [x] Removed Emergent Badge script.
- [x] Removed PostHog script.
- [x] Removed `assets.emergent.sh` script.
- [x] Standardized `index.html` titles.
