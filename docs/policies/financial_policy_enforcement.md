# Financial Policy Enforcement

## Withdrawal Retry Policy (TENANT-POLICY-002)

To prevent spamming PSPs and mitigate risk, the system enforces limits on withdrawal retry attempts via the endpoint:
`POST /api/v1/finance-actions/withdrawals/{tx_id}/retry`

### Error Codes

| Error Code | HTTP Status | Message | Where | Remediation |
| :--- | :--- | :--- | :--- | :--- |
| `LIMIT_EXCEEDED` | 400 | Transaction limit exceeded | `/api/v1/payments/*` | Reduce transaction amount or contact support to increase limits. |
| `TENANT_PAYOUT_RETRY_LIMIT_EXCEEDED` | 422 | Max payout retries exceeded | `/api/v1/finance-actions/withdrawals/{tx_id}/retry` | Do not retry automatically. Investigate reason for failure or create new withdrawal. |
| `TENANT_PAYOUT_COOLDOWN_ACTIVE` | 429 | Payout cooldown active | `/api/v1/finance-actions/withdrawals/{tx_id}/retry` | Wait for cooldown period (default 60s) before retrying. |
| `IDEMPOTENCY_KEY_REQUIRED` | 400 | Idempotency-Key header missing | Critical financial actions | Add `Idempotency-Key: <uuid>` header to request. |
| `IDEMPOTENCY_KEY_REUSE_CONFLICT` | 409 | Idempotency Key reused with different params | Critical financial actions | Generate new key for new request, or retry with same params for same key. |
| `ILLEGAL_TRANSACTION_STATE_TRANSITION` | 400 | Invalid state transition | Transaction State Machine | Verify current transaction state before attempting action. |

### Audit Events

Blocking events are logged to the audit trail with the action:
-   **`FIN_PAYOUT_RETRY_BLOCKED`**: Includes details like `reason` ("limit_exceeded" or "cooldown_active") and the current count/timer.
