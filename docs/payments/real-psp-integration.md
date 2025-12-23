# Real PSP Integration Guide (Stripe)

## Environment Configuration
Ensure the following variables are set in `backend/.env`:
```bash
STRIPE_API_KEY=sk_test_...  # Secret Key from Stripe Dashboard (Test Mode)
```
For the frontend, no specific env var is needed as it relies on the backend for session creation.

## Webhook Setup
The application exposes a webhook endpoint at:
`POST /api/v1/payments/stripe/webhook`

### Local Development
To test webhooks locally, use the Stripe CLI to forward events:
```bash
stripe listen --forward-to localhost:8001/api/v1/payments/stripe/webhook
```
Or use the provided test script `test_stripe.sh` (if available) or the E2E simulation endpoint.

## Local Test Flow
1.  **Initiate Payment**:
    -   Go to Wallet Page.
    -   Select "Deposit", enter amount, click "Pay with Stripe".
2.  **Redirect**:
    -   You will be redirected to the Stripe hosted checkout page.
3.  **Complete Payment**:
    -   Use Stripe test card numbers (e.g., `4242 4242 4242 4242`).
4.  **Return**:
    -   You are redirected back to the Wallet page.
    -   The application polls for status updates.
    -   Balance updates automatically upon success.

## Failure Modes
-   **Signature Verification Failed**: Check `STRIPE_API_KEY` and ensure the webhook secret (if used) matches.
-   **Idempotency Conflict**: If the same session ID is re-processed, the system handles it gracefully via `Transaction` state checks.
-   **Network Error**: Frontend polling retries for 20 seconds before timing out.

## E2E Testing
For CI/CD, we use a simulation endpoint to avoid calling real Stripe APIs during automated tests:
`POST /api/v1/payments/stripe/test-trigger-webhook`
This endpoint is **disabled in production**.
