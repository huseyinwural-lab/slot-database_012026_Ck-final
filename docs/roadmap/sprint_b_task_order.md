# Sprint B: Game Integration & Growth - Task Order

**Status:** ACTIVE
**Goal:** Establish a working Game Loop (Bet/Win) with Ledger integrity and basic Bonus/Risk controls.

---

## 1. B0: Game Provider Contract (Canonical Model)
*   **Task 1.1:** Define SQL Models (`Game`, `GameSession`, `GameRound`, `GameEvent`) in `app/models/game_models.py`.
*   **Task 1.2:** Define Pydantic Schemas for Canonical Webhook (Bet/Win/Rollback) in `app/schemas/game_schemas.py`.

## 2. B1: Game Loop -> Wallet/Ledger (The Engine)
*   **Task 2.1:** Implement `GameEngine` service.
    *   Handle Idempotency (Event ID check).
    *   Handle Locking (Player Wallet lock).
    *   Map Event -> Ledger Delta (Bet = Debit, Win = Credit).
*   **Task 2.2:** Implement `Integrations` Router (`/api/v1/integrations/callback`).

## 3. B5: Mock Provider (Simulation)
*   **Task 3.1:** Create `MockProvider` Router (`/api/v1/mock-provider`).
    *   Endpoints to simulate `launch`, `spin` (which triggers callback to B1).

## 4. B2: Catalog & Frontend
*   **Task 4.1:** API for Game List & Launch URL.
*   **Task 4.2:** Frontend Player - Game Catalog Page.
*   **Task 4.3:** Frontend Player - Game Window (Iframe).

## 5. B3: Bonus MVP (Lite)
*   **Task 5.1:** Update `Player` model with `wagering_remaining`.
*   **Task 5.2:** Update `GameEngine` to deduct from Bonus balance if applicable.

---

**Execution Start:** Immediate.
