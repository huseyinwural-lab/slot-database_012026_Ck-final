# Sprint C - Task 2: Smart Game Engine - Task Order

**Status:** ACTIVE
**Goal:** Implement the deterministic "Math Engine" that powers game outcomes using registered assets.

---

## 1. C2.1: Spin Request Flow
*   **Task 1.1:** Update `mock_provider.py` (Spin Endpoint).
    *   Accept `game_id` (or infer from session).
    *   Call `SlotMath.calculate_spin`.
    *   Call `GameEngine.process_event` (Bet/Win).
    *   Return comprehensive response (Grid, Wins, Audit).

## 2. C2.2: DB Resolve Logic
*   **Task 2.1:** Create `app/services/slot_math.py`.
    *   `load_robot_context(session_id)`: Fetches Binding -> Robot -> Config -> MathAssets.
    *   Validates Active Status.

## 3. C2.3 - C2.5: Deterministic RNG & Logic
*   **Task 3.1:** Implement `generate_grid(reelset, seed)`.
*   **Task 3.2:** Implement `calculate_payout(grid, paytable)`.
    *   Support Center Line logic.

## 4. C2.7: Audit
*   **Task 4.1:** Update `GameEvent` or create `GameRoundAudit` model to store detailed math provenance (hashes, seeds, grid).

---

**Execution Start:** Immediate.
**Owner:** E1 Agent.
