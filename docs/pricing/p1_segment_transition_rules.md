# P1 Segment Transition Rules

**Goal:** Handle lifecycle of segment changes (Upgrade/Downgrade).

## 1. Actors
- **Admin:** Can manually change segment via Backoffice.
- **System:** Can auto-upgrade based on verification (Future scope).

## 2. Transition Logic

### Scenario A: Upgrade (INDIVIDUAL -> DEALER)
- **Effect:** Immediate.
- **Free Quota:** Increases immediately (e.g., 3 -> 50).
- **Packages:** User can now buy/use packages.
- **Active Listings:** Remain active. Renewal will use new Dealer rates.

### Scenario B: Downgrade (DEALER -> INDIVIDUAL)
- **Effect:** Immediate for *new* actions.
- **Free Quota:** Decreases (e.g., 50 -> 3). If usage > 3, no new free listings until usage drops.
- **Existing Packages:** 
    - **Decision:** Do NOT revoke. Rights acquired financially remain valid.
    - **Usage:** User can consume *existing* credits but CANNOT buy new ones.
- **Active Listings:** Remain active.

## 3. Security
- **RBAC:** `pricing:manage_segments` permission required.
- **Audit:** All transitions MUST record `reason` code.
