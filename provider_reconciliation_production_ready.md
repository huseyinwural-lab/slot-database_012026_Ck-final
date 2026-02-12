# Provider Reconciliation Production Ready Spec

**Component:** Reconciliation Worker
**Schedule:** Daily at 02:00 UTC (Configurable)
**Criticality:** P0

## 1. Implementation
- **Worker:** `reconciliation_worker.py` (via Celery/ARQ/Cron).
- **Source A (Internal):** `LedgerTransaction` query grouped by `provider` and `currency`.
- **Source B (External):** `PragmaticAdapter.fetch_transaction_report(date)`.
    - *Note:* Pragmatic API usually provides a CSV or JSON report endpoint.
    - *Fallback:* Manual upload portal for MVP.

## 2. Drift Logic
```python
drift = abs(internal_total - provider_total)
if drift > settings.recon_drift_threshold:
    alert_critical(f"Reconciliation Drift: {drift} {currency}")
```

## 3. Configuration (Environment Based)
| Env | Threshold | Schedule |
|-----|-----------|----------|
| `staging` | 0.00 | Hourly |
| `prod` | 0.01 | Daily |

## 4. Alerting Integration
- **Success:** Log INFO `Reconciliation PASS: Match 100%`.
- **Failure:** Log CRITICAL + Increment `provider_wallet_drift_detected_total`.
