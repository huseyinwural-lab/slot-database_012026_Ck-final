# Secrets & Configuration Checklist (D4-1)

**Status:** PASS
**Date:** 2025-12-26

## 1. Secrets Inventory
Based on `config.py` analysis and sanitized dump.

| Secret Name | Usage | Status | Notes |
|-------------|-------|--------|-------|
| `JWT_SECRET` | Auth Token Signing | **PASS** | Set in env, not default in prod |
| `DATABASE_URL` | DB Connection | **PASS** | Injected securely |
| `STRIPE_API_KEY` | Payment Processing | **PASS** | Starts with `sk_` |
| `STRIPE_WEBHOOK_SECRET` | Webhook Verify | **PASS** | Starts with `whsec_` |
| `ADYEN_API_KEY` | Payment Processing | **PASS** | Present |
| `ADYEN_HMAC_KEY` | Webhook Verify | **PASS** | Present |
| `AUDIT_EXPORT_SECRET` | Archive Integrity | **PASS** | Changed from default |
| `AUDIT_S3_SECRET_KEY` | Long-term Storage | **PASS** | Injected |

## 2. Configuration Hardening
- [x] **Debug Mode:** Disabled in Prod (`DEBUG=False`).
- [x] **CORS:** Strict allowlist enforced (No `*`).
- [x] **Admin Seeding:** Disabled (`SEED_ON_STARTUP=False`).
- [x] **Test Payments:** Disabled (`ALLOW_TEST_PAYMENT_METHODS=False`).

## 3. Waivers
*None. All critical secrets are accounted for.*

## 4. Evidence
- **Sanitized Dump:** `/app/artifacts/d4_env_dump_sanitized.txt`
