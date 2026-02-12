# Provider Observability Plan

**Namespace:** `provider`

## 1. Metrics (Prometheus)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `provider_requests_total` | Counter | `provider`, `method`, `status` | Incoming callbacks. |
| `provider_latency_seconds` | Histogram | `provider`, `method` | Processing time (Adapter + Engine). |
| `provider_signature_failures_total` | Counter | `provider` | Auth failures (Possible attack). |
| `provider_wallet_balance_mismatch_total` | Counter | `provider` | Post-recon drift. |

## 2. Logs
-   **Structured Log:** `ProviderRequest`
    ```json
    {
      "event": "provider_callback",
      "provider": "pragmatic",
      "method": "bet",
      "tx_id": "ref_123",
      "user_id": "u_456",
      "duration_ms": 45,
      "risk_verdict": "ALLOW"
    }
    ```

## 3. Alerts
-   **High Error Rate:** `rate(provider_requests_total{status="5xx"}) > 5%`.
-   **Slow Response:** `p99 > 1s` (Provider might timeout).
