#!/bin/bash

ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MDU2OTkxYy04YjU4LTRlYTUtOGJhNC0wOTEyMDdjMDZhMzkiLCJlbWFpbCI6ImFkbWluQGNhc2luby5jb20iLCJ0ZW5hbnRfaWQiOiJkZWZhdWx0X2Nhc2lubyIsInJvbGUiOiJTdXBlciBBZG1pbiIsImV4cCI6MTc2NjYyMjg1MH0.s_GiyhYFIkdENyob5d7rReejbjZ6kkemtYAh5PczJlo"
DEPOSIT_TX_ID="e3dac1da-90c9-4b48-b41b-28bac985eedc"
WITHDRAWAL_TX_ID="362228c2-92e6-4c27-b9e6-3ef473f29db7"
BASE_URL="http://localhost:8001"
ARTIFACTS_DIR="/app/artifacts/pr2-proof"

mkdir -p $ARTIFACTS_DIR

echo "=== Running PR2 Verification ==="

# T2.1 Stripe Webhook Signature Smoke Test
echo "Testing Stripe Webhook Signature..."
curl -v -X POST "$BASE_URL/api/v1/payments/stripe/webhook" \
  -H "stripe-signature: invalid_signature" \
  -d '{}' > "$ARTIFACTS_DIR/stripe-webhook-smoke.txt" 2>&1
echo "Stripe Test Done."

# T2.2 Adyen Webhook Replay Smoke Test
# We use the DEPOSIT_TX_ID which is already 'completed' in setup.
# Sending a success webhook for it should trigger replay logic (200 OK, Log replay).
echo "Testing Adyen Webhook Replay..."
curl -v -X POST "$BASE_URL/api/v1/payments/adyen/webhook" \
  -H "Content-Type: application/json" \
  -d "{\"notificationItems\":[{\"NotificationRequestItem\":{\"eventCode\":\"AUTHORISATION\",\"merchantReference\":\"$DEPOSIT_TX_ID\",\"success\":\"true\",\"pspReference\":\"REPLAY_TEST_REF\"}}]}" \
  > "$ARTIFACTS_DIR/adyen-webhook-smoke.txt" 2>&1
echo "Adyen Test Done."

# T2.3 Refund Smoke Test
# We use the same DEPOSIT_TX_ID. It is completed. Now we refund it.
echo "Testing Refund Flow..."
curl -v -X POST "$BASE_URL/api/v1/finance/deposits/$DEPOSIT_TX_ID/refund" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "PR2 Smoke Test Verification"}' \
  > "$ARTIFACTS_DIR/refund-smoke.txt" 2>&1
echo "Refund Test Done."

# T3 Payout Gating Smoke Test
# We run the python script that mocks PROD environment
echo "Testing Payout Gating (Prod Simulation)..."
export ADMIN_TOKEN
export WITHDRAWAL_TX_ID
cd /app/backend
python3 verify_prod_gating.py > "$ARTIFACTS_DIR/payout-gating-smoke.txt" 2>&1
echo "Payout Gating Test Done."

echo "=== All Proofs Generated ==="
ls -l $ARTIFACTS_DIR
