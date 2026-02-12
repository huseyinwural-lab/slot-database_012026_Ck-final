# Staging Soak Test Status

**Status:** EXECUTION ACTIVE 🌊
**Start Date:** 2026-02-16
**Target Duration:** 72 Hours (Minimum)

## 1. Scope
- **Provider:** Pragmatic Play (Mocked via Load Test)
- **Features:** Wallet Sync, Risk Throttling, Reconciliation
- **Environment:** Staging (Config Parity with Prod)

## 2. Execution Plan
- [x] **Config Lock:** `prod_guard.py` active.
- [ ] **Traffic:** `load_test_provider.py` running in background.
- [ ] **Recon:** Daily job scheduled.
- [ ] **Alerts:** Validated via `alert_validation_helper.py`.

## 3. Metrics to Watch
- `provider_wallet_drift_detected_total` (Must be 0)
- `bet_rate_limit_exceeded_total` (Should match Risk rules)
- `p99_latency` (Target < 200ms)
