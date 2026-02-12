# Sprint 1 Exit Report

**Sprint:** Faz 6C - Sprint 1 (Risk Layer)
**Date:** 2026-02-16
**Status:** COMPLETED ✅

## 1. Deliverables Verified
- [x] **Database Schema:** `risk_profiles` table created (Migration `20260216_01`).
- [x] **Risk Service:** Implemented scoring, rule evaluation, and velocity tracking.
- [x] **Integration:** `WithdrawalService` (via `player_wallet.py`) enforces risk blocks.
- [x] **Storage:** Redis `InMemoryRedis` patched for pipeline support; Velocity keys active.
- [x] **Observability:** Metrics (`risk_blocks`, `risk_flags`, `risk_score_updates`) instrumented.

## 2. Testing Results
- **Unit Tests:** `test_risk_rules_v1.py` PASS.
- **Integration Tests:** `test_withdrawal_risk_blocking.py` PASS.
    - Verified HIGH risk users get `403 RISK_BLOCK`.
    - Verified LOW risk users proceed.

## 3. Known Issues / Technical Debt
- **Redis Mock:** We are running on `InMemoryRedis` in this environment. Production requires real Redis.
- **Rules Hardcoded:** Rules are currently hardcoded in `RiskService._evaluate_rules`. Future sprints should move these to DB/Config.
- **Decay:** No score decay mechanism yet (Risk scores only go up).

## 4. Next Steps (Sprint 2)
- Implement `Bet` velocity throttling.
- Build Admin Dashboard for manual review queue.
- Implement Score Decay job.
