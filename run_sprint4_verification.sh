#!/bin/bash
ARTIFACTS_DIR="/app/artifacts/sprint4-release-smoke"
OPS_PROOF_DIR="/app/artifacts/sprint4-ops-proof"
REFUND_PROOF_DIR="/app/artifacts/sprint4-refund-proof"

mkdir -p $ARTIFACTS_DIR
mkdir -p $OPS_PROOF_DIR
mkdir -p $REFUND_PROOF_DIR

echo "=== 1. E2E Release Smoke ==="
cd /app/e2e
# We use --reporter=line to avoid massive output in CI logs, but we configured html in config.
npx playwright test tests/release-smoke-money-loop.spec.ts > "$ARTIFACTS_DIR/playwright_log.txt" 2>&1
EXIT_E2E=$?
echo "E2E Exit Code: $EXIT_E2E"
if [ $EXIT_E2E -ne 0 ]; then
    echo "E2E Failed. Check logs."
    cat "$ARTIFACTS_DIR/playwright_log.txt"
fi

# Copy report if exists
if [ -d "playwright-report" ]; then
    cp -r playwright-report "$ARTIFACTS_DIR/"
fi

echo "=== 2. Ops Thresholds & Metrics ==="
cd /app/backend
pytest -v tests/test_ops_dashboard_thresholds.py > "$OPS_PROOF_DIR/backend-tests.txt" 2>&1
EXIT_OPS=$?
echo "Ops Tests Exit Code: $EXIT_OPS"

# Generate Dashboard JSON
# Need a token
export TOKEN=$(python3 get_admin_token.py 2>/dev/null | grep -v "INFO" | grep -v "ROLLBACK" | tail -n 1)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/v1/ops/dashboard > "$OPS_PROOF_DIR/ops_dashboard.json"

echo "=== 3. Refund Hardening ==="
pytest -v tests/test_refund_flow.py > "$REFUND_PROOF_DIR/refund-tests.txt" 2>&1
EXIT_REFUND=$?
echo "Refund Tests Exit Code: $EXIT_REFUND"

echo "=== Summary ==="
echo "E2E: $EXIT_E2E"
echo "Ops: $EXIT_OPS"
echo "Refund: $EXIT_REFUND"
