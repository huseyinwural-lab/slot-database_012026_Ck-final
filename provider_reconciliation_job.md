# Provider Reconciliation Job Spec

**Frequency:** Daily (e.g., 02:00 UTC)
**Goal:** Detect financial drift between Internal Ledger and Provider Records.

## 1. Logic
1.  **Fetch Provider Report:** Simulate fetching a transaction CSV/API from Pragmatic (Mocked for now).
2.  **Fetch Internal Ledger:** Query `LedgerTransaction` for the same period.
3.  **Aggregation:** Group by `currency` and `type` (Bet/Win).
4.  **Comparison:**
    -   `Drift = Abs(Provider_Total - Internal_Total)`
    -   If `Drift > 0.01`: Raise CRITICAL Alert.

## 2. Implementation
-   **Script:** `backend/app/scripts/recon_provider.py`
-   **Storage:** `ReconciliationReport` table.

## 3. Alerting
-   **Metric:** `provider_wallet_drift_amount`
-   **Threshold:** > 0.01
