#!/bin/bash
ARTIFACTS_DIR="/app/artifacts/rc-proof"
mkdir -p $ARTIFACTS_DIR

echo "=== 1. E2E RC Smoke (Headless & Determinstic) ==="
cd /app/e2e
npx playwright test tests/release-smoke-money-loop.spec.ts --reporter=line > "$ARTIFACTS_DIR/e2e-release-smoke.txt" 2>&1
EXIT_E2E=$?
echo "E2E Exit Code: $EXIT_E2E"

if [ $EXIT_E2E -eq 0 ]; then
    echo "E2E PASS"
else
    echo "E2E FAIL - Check logs"
    cat "$ARTIFACTS_DIR/e2e-release-smoke.txt"
fi

echo "=== 2. Backend Regression ==="
cd /app/backend
pytest -v tests/test_payout_real_provider.py tests/test_refund_flow.py tests/test_ops_dashboard_thresholds.py > "$ARTIFACTS_DIR/backend-regression.txt" 2>&1
EXIT_BACKEND=$?
echo "Backend Exit Code: $EXIT_BACKEND"

echo "=== 3. Ops Dashboard Snapshot ==="
export TOKEN=$(python3 get_admin_token.py 2>/dev/null | grep -v "INFO" | grep -v "ROLLBACK" | tail -n 1)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/v1/ops/dashboard > "$ARTIFACTS_DIR/ops_dashboard.json"

echo "=== 4. Proof Pack Summary ==="
ls -l $ARTIFACTS_DIR
