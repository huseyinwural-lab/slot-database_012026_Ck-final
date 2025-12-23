# Financial Policy Enforcement

## Withdrawal Retry Policy (TENANT-POLICY-002)

To prevent spamming PSPs and mitigate risk, the system enforces limits on withdrawal retry attempts via the endpoint:
`POST /api/v1/finance-actions/withdrawals/{tx_id}/retry`

### Error Codes

| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| **422 Unprocessable Entity** | `PAYMENT_RETRY_LIMIT_EXCEEDED` | The maximum number of retry attempts (defined by `tenant.payout_retry_limit`) has been reached. |
| **429 Too Many Requests** | `PAYMENT_COOLDOWN_ACTIVE` | The required cooldown period (defined by `tenant.payout_cooldown_seconds`) since the last attempt has not yet passed. |

### Audit Events

Blocking events are logged to the audit trail with the action:
-   **`FIN_PAYOUT_RETRY_BLOCKED`**: Includes details like `reason` ("limit_exceeded" or "cooldown_active") and the current count/timer.
