# Webhook Failure Playbook

## 1. Signature Verification Failure
**Symptom:** `401 Unauthorized` responses to `/api/v1/payments/*/webhook`.
**Alert:** `Log error: "Webhook Signature Verification Failed"`
**Action:**
1. Check `ADYEN_HMAC_KEY` or `STRIPE_WEBHOOK_SECRET` in environment variables.
2. Verify if the provider (Adyen/Stripe) has rotated keys.
3. If persistent, temporarily enable logging of raw headers (careful with PII) to debug.

## 2. Replay Storm
**Symptom:** Multiple webhooks for same `provider_event_id`.
**Alert:** `Log info: "Replay detected"` count > 100/min.
**Action:**
1. This is usually harmless (Idempotency handles it).
2. If load is high, block IP or contact provider.

## 3. Rate Limit
**Symptom:** Provider returns 429 when we call them (e.g. during Payout).
**Alert:** `HTTP 429` in logs.
**Action:**
1. Check `PayoutAttempt` table for stuck items.
2. Manually retry after backoff.
