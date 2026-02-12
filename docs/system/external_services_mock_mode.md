# External Services Mock Mode

## Strategy
All external services default to **MOCK** mode unless explicitly configured otherwise via Environment Variables.

## Configuration Source
`/app/backend/config.py`

## Services
| Service | Env Var | Default | Mock Behavior |
|---------|---------|---------|---------------|
| **Resend (Email)** | `RESEND_API_KEY` | None | Logs email to console/logger. |
| **Twilio (SMS)** | `TWILIO_ACCOUNT_SID` | None | Logs SMS content. |
| **Stripe (Payments)** | `STRIPE_MOCK` | `False`* | Uses `StripeMock` wrapper if enabled or keys missing. (*Default depends on key presence) |
| **Redis** | `MOCK_REDIS` | `True` | Uses in-memory dict/list for rate limits. |
| **Pragmatic Play** | N/A | N/A | Uses `GameSimulator` adapter. |

## Production Parity
In Production (`ENV=prod`):
- `validate_prod_secrets()` ensures critical keys (Stripe, Adyen) are present.
- Mock toggles (like `KYC_MOCK_ENABLED`) MUST be false.

## Action Item
Ensure `MOCK_EXTERNAL_SERVICES=true` is set in local/CI `.env`.
