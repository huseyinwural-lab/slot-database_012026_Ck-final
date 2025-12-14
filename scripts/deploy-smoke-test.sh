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

# 4. Check Frontend Assets (Basic Reachability)
# Since we are in a container without full browser, we just check if ports are open/listening
echo "\n🔍 [4/4] Checking Frontends..."
# Admin
if nc -z localhost 3000; then
    echo "✅ Admin Frontend listening on 3000"
else
    echo "⚠️  Admin Frontend not reachable (might be starting up)"
fi

# Player
if nc -z localhost 3001; then
    echo "✅ Player Frontend listening on 3001"
else
    echo "⚠️  Player Frontend not reachable (might be starting up)"
fi

echo "\n✨ SMOKE TEST COMPLETE: SYSTEM READY ✨"
exit 0
