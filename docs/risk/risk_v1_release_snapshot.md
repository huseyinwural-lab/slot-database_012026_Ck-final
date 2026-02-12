# Risk V1 Release Snapshot (Production Baseline)

**Release:** Risk Layer V1 (Foundation)
**Status:** ACTIVE 🟢
**Date:** 2026-02-16
**Version:** v1.0.0-risk

## 1. Artifacts Locked
- **Database Schema:** `risk_profiles` (Migration Hash: `20260216_01_risk_profile`)
- **Service Logic:** `RiskService` (Rule-based engine active)
- **Integration:** Withdrawal Guard in `player_wallet.py` (Enforcing `BLOCK`/`FLAG`)
- **Tests:** CI Run ID `RISK-SPRINT1-VERIFY-001` (Pass)

## 2. Infrastructure Dependencies
| Component | Usage | Criticality | Fail-Safe Behavior |
|-----------|-------|-------------|--------------------|
| **PostgreSQL** | User Profiles, Score Persistence | HIGH | Transaction Fail (Safe) |
| **Redis** | Velocity Counters (Sliding Window) | HIGH | **MEDIUM Risk Fallback** (Soft Flag) |

## 3. Configuration
- **Enforcement Mode:** Withdrawal Pipeline ONLY.
- **Thresholds:**
    -   `> 70`: BLOCK
    -   `> 40`: FLAG (Manual Review)
    -   `< 40`: ALLOW

## 4. Known Limitations
- **Betting:** No real-time blocking on bets yet (Sprint 2).
- **Rules:** Hardcoded in service (not dynamic DB rules yet).
- **Scoring:** Only increases (Decay job planned for future).

**Status:** PRODUCTION READY.
