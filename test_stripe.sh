#!/bin/bash
EMAIL="teststripe_$(date +%s)@example.com"
PASS="password123"
TENANT="default_casino"
API="http://localhost:8001"

# Register
echo "Registering..."
curl -s -X POST "$API/api/v1/auth/player/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASS\", \"username\": \"stripeuser\", \"tenant_id\": \"$TENANT\"}" > /dev/null

# Login
echo "Logging in..."
LOGIN_RES=$(curl -s -X POST "$API/api/v1/auth/player/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASS\", \"tenant_id\": \"$TENANT\"}")

TOKEN=$(echo $LOGIN_RES | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "Login failed"
  exit 1
fi

echo "Creating Session..."
SESSION_RES=$(curl -s -X POST "$API/api/v1/payments/stripe/checkout/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"amount": 20.0, "currency": "USD"}')

SESSION_ID=$(echo $SESSION_RES | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")

echo "Session ID: $SESSION_ID"

if [ -n "$SESSION_ID" ]; then
    echo "Checking Status..."
    curl -s -X GET "$API/api/v1/payments/stripe/checkout/status/$SESSION_ID" \
      -H "Authorization: Bearer $TOKEN"
else
    echo "Failed to get session ID: $SESSION_RES"
fi
