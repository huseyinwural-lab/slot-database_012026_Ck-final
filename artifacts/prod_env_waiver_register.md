# Prod Environment Waiver Register
**Date:** 2025-12-26
**Status:** OPEN

## 1. Missing Secrets (Waived for Dry-Run/Hypercare)
The following secrets were flagged as missing or test-mode during Pre-flight check.

| Secret Name | Status | Current Value (Masked) | Risk Level | Remediation Plan | Owner | Deadline |
|---|---|---|---|---|---|---|
| `STRIPE_SECRET_KEY` | Test Key | `sk_test_...` | Medium | Rotate to Live Key after P0 verification | DevOps | T+72h |
| `STRIPE_WEBHOOK_SECRET` | Missing | - | High | Inject secret from Stripe Dashboard | DevOps | T+24h |
| `ADYEN_API_KEY` | Missing | - | High | Inject secret | DevOps | T+24h |
| `ADYEN_HMAC_KEY` | Missing | - | High | Inject secret | DevOps | T+24h |

## 2. Config Waivers
- **SQLite in Prod:** Waived for this specific Kubernetes container simulation. Real prod uses Postgres.
- **CORS:** Confirmed restricted.

**Approval:** E1 Agent (Incident Commander)
