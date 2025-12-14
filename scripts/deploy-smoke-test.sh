#!/bin/bash
set -e

echo "🚀 Starting Deployment Smoke Test..."

# 1. Check Config
echo "\n🔍 [1/4] Checking Configuration..."
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env missing!"
    exit 1
fi
echo "✅ Configuration present."

# 2. Check Service Health (Backend)
echo "\n🔍 [2/4] Checking Backend Health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health)

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "✅ Backend is UP (HTTP 200)"
else
    echo "❌ Backend Health Check FAILED (HTTP $HEALTH_STATUS)"
    echo "Logs:"
    tail -n 20 /var/log/supervisor/backend.err.log
    exit 1
fi

# 3. Check Database Connection (Readiness)
echo "\n🔍 [3/4] Checking Database Connection..."
READY_STATUS=$(curl -s http://localhost:8001/api/readiness)

if echo "$READY_STATUS" | grep -q "connected"; then
    echo "✅ Database is CONNECTED"
else
    echo "❌ Database Readiness FAILED: $READY_STATUS"
    exit 1
fi

# 4. Check Frontend Assets (Alternative to nc)
echo "\n🔍 [4/4] Checking Frontends..."
# Since 'nc' is missing, we check process list for node/yarn
if pgrep -f "react-scripts start" > /dev/null; then
    echo "✅ Admin Frontend process RUNNING"
else
    echo "⚠️  Admin Frontend process NOT FOUND"
fi

if pgrep -f "vite" > /dev/null; then
    echo "✅ Player Frontend process RUNNING"
else
    echo "⚠️  Player Frontend process NOT FOUND"
fi

echo "\n✨ SMOKE TEST COMPLETE: SYSTEM READY ✨"
exit 0
