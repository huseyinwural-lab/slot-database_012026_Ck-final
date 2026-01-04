# Webhooks (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Payments Engineering / Ops  

This document consolidates webhook operational requirements and the deterministic behaviors expected in staging/prod.

---

## 1) What a webhook must guarantee

### 1.1 Authenticity (signature verification)
- Stripe: verify `Stripe-Signature`
- Adyen: verify HMAC signature (per Adyen webhook spec)

**Rule:** signature verification must be enabled in staging/prod.

### 1.2 Idempotency
Webhook deliveries can be repeated.

**Rule:** processing must be idempotent based on provider event id / notification id.

### 1.3 Observability
Every webhook request should have:
- `request_id`
- `tenant_id` (when applicable)
- structured log fields

See:
- `/docs/ops/log_schema.md`

---

## 2) API endpoints (typical)

- `POST /api/v1/payments/stripe/webhook`
- `POST /api/v1/payments/adyen/webhook`

See also:
- `/docs/new/en/api/payments.md`

---

## 3) Retry strategy & failure handling

### 3.1 Provider retries
Providers retry on non-2xx and timeouts.

Operational guidance:
- Return 2xx only after successful verification and safe persistence.
- If DB is down, prefer failing fast (provider will retry).

### 3.2 Common failure modes
- Signature mismatch
- Clock skew (signature timestamp windows)
- Payload schema changes
- Duplicate events

---

## 4) Tenant scope

Webhook tenant resolution depends on how your platform maps provider accounts to tenants.

Rules:
- Never accept tenant overrides from non-owner admins.
- Avoid using `X-Tenant-ID` for public webhook endpoints unless you have a secure mapping.

---

## 5) Incident playbook (quick)

1) Confirm provider delivery attempts (Stripe/Adyen dashboards)
2) Check backend logs for `request_id` and webhook event name
3) Verify signature secret configuration
4) If processing is failing, contain: stop payout automation if needed

Legacy references:
- `/docs/ops/webhook-failure-playbook.md`
- `/docs/payments/STRIPE_WEBHOOKS.md`
- `/docs/payments/ADYEN_WEBHOOKS.md`
