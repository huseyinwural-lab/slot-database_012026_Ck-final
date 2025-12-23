# Adyen Payment Integration

## Overview
This integration allows players to deposit funds using Adyen Payment Links. It supports a mock mode for development and testing without real Adyen credentials.

## Architecture

### Backend
- **Service**: `app.services.adyen_psp.AdyenPSP`
  - Handles `create_payment_link` and `verify_webhook_signature`.
  - In `dev` mode with `allow_test_payment_methods=True`, it returns a mock URL that immediately redirects to the success page.
- **Routes**: `app.routes.adyen_payments`
  - `POST /checkout/session`: Creates a pending transaction and an Adyen Payment Link.
  - `POST /webhook`: Handles `AUTHORISATION` events from Adyen to complete transactions.
  - `POST /test-trigger-webhook`: Simulation endpoint for CI/CD E2E testing.
- **Configuration**:
  - `adyen_api_key`: API Key (optional in dev).
  - `adyen_merchant_account`: Merchant Account Code.
  - `adyen_hmac_key`: Webhook HMAC Key.

### Frontend
- **Page**: `WalletPage.jsx`
- **Flow**:
  1. User selects "Adyen" and enters amount.
  2. Frontend calls `/checkout/session`.
  3. Backend returns `{ url: "..." }`.
  4. Frontend redirects user to Adyen (or mock URL).
  5. Adyen redirects user back to `/wallet?provider=adyen&resultCode=Authorised`.
  6. Frontend detects `resultCode` and shows success message.

## Testing

### E2E Test
- `e2e/tests/adyen-deposit.spec.ts`
- Verifies the full flow: Register -> Deposit -> Mock Redirect -> Webhook Simulation -> Balance Update.

### Simulation
You can simulate a successful payment manually:
```bash
curl -X POST http://localhost:8001/api/v1/payments/adyen/test-trigger-webhook \
  -H "Content-Type: application/json" \
  -d '{"tx_id": "YOUR_TX_ID", "success": true}'
```

## Production Setup
1. Set `ADYEN_API_KEY`, `ADYEN_MERCHANT_ACCOUNT`, `ADYEN_HMAC_KEY` in environment variables.
2. Ensure `ALLOW_TEST_PAYMENT_METHODS=False`.
3. Configure Adyen Customer Area to send webhooks to `https://your-domain.com/api/v1/payments/adyen/webhook`.
