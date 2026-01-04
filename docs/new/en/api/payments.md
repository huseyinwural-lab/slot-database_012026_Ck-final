# Payments API (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Payments Engineering  

This document provides a stable overview of the payments-related API surface.

> Detailed provider-specific procedures (Stripe/Adyen), webhooks, and incident playbooks are currently documented under legacy `/docs/payments/` and `/docs/ops/`.

---

## 1) Base paths

Typical paths:
- `/api/v1/payments/*`
- `/api/v1/payouts/*` (if present in your environment)

---

## 2) Webhooks (external → backend)

### 2.1 Stripe
- `POST /api/v1/payments/stripe/webhook`

### 2.2 Adyen
- `POST /api/v1/payments/adyen/webhook`

Operational notes:
- Webhook endpoints are usually **high-volume**; rate limits (if any) should be set accordingly.
- Webhook signature verification must be enabled in staging/prod.

Legacy references:
- `/docs/payments/STRIPE_WEBHOOKS.md`
- `/docs/payments/ADYEN_WEBHOOKS.md`

---

## 3) Tenant scope & isolation

Rules:
- Tenant-scoped payment policy is resolved via `get_current_tenant_id()`.
- Platform owner may impersonate tenant via `X-Tenant-ID`.
- Non-owner header usage is forbidden.

See:
- `/docs/new/en/api/tenants.md`
- `/docs/new/en/admin/roles-permissions.md`

---

## 4) Common failure modes (ops quick map)

- Webhook signature mismatch
- Provider timeout / retry storms
- Payout status polling flakiness

Legacy incident/runbook references:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/ops/dr_runbook.md`
