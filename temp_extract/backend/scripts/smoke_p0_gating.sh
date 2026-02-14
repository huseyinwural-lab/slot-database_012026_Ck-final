#!/bin/bash
# P0-1 Gating Smoke Test
# We reuse the existing python script but ensure we pass required env vars.
# We also need to patch secrets because now startup validation will fail if ENV=prod!
# Wait, verify_prod_gating.py mocks ENV=prod inside the script using patch.
# But does it mock the secrets for the VALIDATION check?
# The validation runs on import of server.py if we put it at top level.
# I put `settings.validate_prod_secrets()` in `server.py`.
# When `verify_prod_gating.py` imports `server`, validation runs.
# Since the actual ENV is `dev` (from .env file), validation PASSES on import.
# Then inside the script, we patch ENV=prod for the REQUEST logic.
# So validation won't block the script execution. Correct.

export ADMIN_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MDU2OTkxYy04YjU4LTRlYTUtOGJhNC0wOTEyMDdjMDZhMzkiLCJlbWFpbCI6ImFkbWluQGNhc2luby5jb20iLCJ0ZW5hbnRfaWQiOiJkZWZhdWx0X2Nhc2lubyIsInJvbGUiOiJTdXBlciBBZG1pbiIsImV4cCI6MTc2NjYyMjg1MH0.s_GiyhYFIkdENyob5d7rReejbjZ6kkemtYAh5PczJlo"
export WITHDRAWAL_TX_ID="362228c2-92e6-4c27-b9e6-3ef473f29db7"

cd /app/backend
python3 verify_prod_gating.py > /app/artifacts/sprint4-p0-proof/gating_smoke.txt 2>&1
cat /app/artifacts/sprint4-p0-proof/gating_smoke.txt
