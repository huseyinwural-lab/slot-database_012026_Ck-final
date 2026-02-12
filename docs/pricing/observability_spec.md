# Observability Specification (P0.5)

**Goal:** Visibility into pricing reliability and business performance.

## 1. Business Metrics (Prometheus/Datadog)

### `pricing_commit_total`
- **Type:** Counter
- **Labels:** `status` (success, failed), `segment` (individual, gallery), `action` (renew, upgrade).
- **Goal:** Track throughput and conversion.

### `pricing_allocation_total`
- **Type:** Counter
- **Labels:** `type` (FREE_QUOTA, PAID_PACKAGE, PAY_AS_YOU_GO).
- **Goal:** Monitor consumption patterns.

## 2. Operational Metrics

### `pricing_idempotency_hits`
- **Type:** Counter
- **Goal:** Detect retry storms or frontend bugs.

### `pricing_latency_seconds`
- **Type:** Histogram
- **Labels:** `step` (calculation, ledger_write, response).
- **Goal:** P95 < 200ms.

## 3. Logs (Structured)
Format: JSON
Required Fields:
- `trace_id`
- `tenant_id`
- `listing_id`
- `pricing_verdict` (The final calculated price)
- `applied_rules` (List of rule IDs applied)
