#!/bin/bash
EMAIL="teststripe_$(date +%s)@example.com"
PASS="password123"
TENANT="default_casino"
API="http://localhost:8001"

# Register
echo "Registering..."
curl -s -X POST "$API/api/v1/auth/player/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASS\", \"username\": \"stripeuser\", \"tenant_id\": \"$TENANT\"}"

# Login
echo "Logging in..."
LOGIN_RES=$(curl -s -X POST "$API/api/v1/auth/player/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASS\", \"tenant_id\": \"$TENANT\"}")

TOKEN=$(echo $LOGIN_RES | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "Login failed: $LOGIN_RES"
  exit 1
fi

echo "Token obtained."

# Call Checkout Session
echo "Creating Session..."
curl -s -X POST "$API/api/v1/payments/stripe/checkout/session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"amount": 20.0, "currency": "USD"}'
