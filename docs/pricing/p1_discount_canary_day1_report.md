# P1 Discount Canary Day 1 Report

**Date:** 2026-02-15
**Status:** MONITORING

## 1. Rollout Scope
- **Tenants:** `["demo-tenant-1"]` (Internal QA/Staff)
- **Traffic %:** 1% of total pricing requests.

## 2. Key Metrics (Last 24h)

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Total Gross Revenue** | $0.00 | N/A | ℹ️ INFO |
| **Total Discounts Applied** | $0.00 | Max 20% of Gross | ✅ OK |
| **Net Revenue** | $0.00 | Gross - Discount | ✅ OK |
| **Error Rate (Pricing)** | 0.00% | < 0.1% | ✅ OK |
| **Ledger Mismatches** | 0 | 0 | ✅ OK |

## 3. Incidents / Anomalies
- None reported in initial smoke tests.

## 4. Decision
- [ ] Expand to 10% Traffic
- [ ] Rollback
- [x] Continue Monitoring
