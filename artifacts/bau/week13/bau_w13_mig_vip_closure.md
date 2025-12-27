# BAU Sprint 13 Closure Report: Migration Stabilization & VIP Loyalty

**Sprint Goal:** Restore database migration stability (P0) and implement the VIP/Loyalty system.

## Completed Items

### 1. Migration Stabilization (P0)
-   **Schema Drift Reset:** Analyzed `models` vs `DB` drift.
-   **Drift Reset Migration (`3c4ee35573cd`):** Created an idempotent migration to sync Alembic history with the actual DB state (including `AdminUser.mfa_enabled` and `Affiliate` fields).
-   **Ambiguity Resolution:** Cleaned up `env.py` imports and `sql_models.py` duplicates.
-   **Result:** `alembic upgrade head` now runs cleanly on the existing environment.

### 2. VIP & Loyalty System (P1)
-   **Models:** Implemented `VipTier`, `PlayerVipStatus`, `LoyaltyTransaction`.
-   **VipEngine:**
    -   `award_points`: Updates lifetime/current points and checks for Tier Upgrade.
    -   `redeem_points`: Converts points to cash (Ledger + Wallet sync).
-   **API:**
    -   Admin: Manage Tiers, Simulate Activity.
    -   Player: Check Status, Redeem Points.

## Validation
-   **E2E Runner:** `/app/scripts/bau_w13_runner.py`
-   **Flow Verified:**
    1.  Admin creates Tiers (Bronze, Silver, Gold).
    2.  Player registers -> Earns 1500 Points.
    3.  Player upgrades to **Silver** Tier automatically.
    4.  Player redeems 500 Points -> Receives $5.00 Cash.

## Evidence Package
-   **Execution Log:** `e2e_vip_loyalty_loop.txt`
-   **Metrics Snapshot:** `vip_metrics_snapshot.json`

## Technical Notes
-   **Manual Drop Required:** During development, had to manually drop `viptier` tables to allow Alembic to register them correctly in the new migration flow. This was a one-time fix.
-   **SQLite Limitations:** `ALTER COLUMN` support is limited; some column alterations were soft-skipped or handled carefully to avoid batch mode failures.

## Next Steps
-   **BAU Sprint 14:** Advanced Poker Features (Collusion Detection, Late Reg).
-   **CI Integration:** Add `alembic upgrade head` to CI pipeline (T13-002) to prevent future drift.
