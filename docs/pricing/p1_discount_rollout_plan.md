# P1 Discount Rollout Plan

**Strategy:** Canary -> Tenant Whitelist -> Global.

## Phase 1: Internal (Canary)
- **Target:** `tenant_id` IN (`internal-qa`, `demo-account`).
- **Duration:** 24h.
- **Checks:** Logs, Metrics, Admin Report accuracy.

## Phase 2: Pilot (Whitelist)
- **Target:** 5 selected real tenants (low volume).
- **Duration:** 48h.
- **Checks:** Support tickets, "My Bill" accuracy.

## Phase 3: Global (General Availability)
- **Target:** All tenants.
- **Rollback Trigger:**
  - Error rate > 1%.
  - P95 Latency > 500ms.
  - NGR drop > 10% (unexpected).

## Config
- Feature Flag: `PRICING_ENGINE_V2_TENANTS` (List of UUIDs) or `PRICING_ENGINE_V2_GLOBAL` (Bool).
