# Provider Failure Mode Matrix

**Standard:** All provider errors map to specific HTTP Codes + Internal Error Codes.

| Scenario | HTTP Status | Provider Error Code | Internal Action |
|----------|-------------|---------------------|-----------------|
| **Signature Invalid** | 403 Forbidden | `100` (Internal) | Block request, Alert Security. |
| **Insufficient Funds** | 200 OK (Logic Error) | `1` (Insuff. Funds) | No Debit, Return Error payload. |
| **Player Not Found** | 200 OK (Logic Error) | `2` (Player Not Found) | Return Error payload. |
| **Idempotency Hit** | 200 OK | `0` (Success) | Return cached response. |
| **Redis Risk Down** | 200 OK | `0` (Success) | Fail-Open (Allow Bet) or Fail-Safe (Medium Risk). |
| **DB Lock Timeout** | 500 Internal | `100` (Internal) | Retry (Provider side). |
| **Rate Limit** | 429 Too Many Requests | `50` (Temp Error) | Retry later. |

## Recovery Strategy
-   **5xx Errors:** Provider should retry with exponential backoff.
-   **4xx Errors:** Provider should NOT retry (Fix payload).
-   **Logic Errors:** Provider should show error to user.
