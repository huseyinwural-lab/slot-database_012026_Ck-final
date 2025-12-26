# Sprint C: Controlled Casino - Task Order

**Status:** ACTIVE
**Goal:** Replace random mock logic with deterministic Math Engine (Robot Registry).

---

## 1. C1 & C2: Robot Registry & Math Assets
*   **Task 1.1:** Create `app/models/robot_models.py`.
    *   `RobotDefinition`, `MathAsset`, `GameRobotBinding`.
*   **Task 1.2:** Alembic Migration.
*   **Task 1.3:** Seed Script `scripts/seed_robots.py`.
    *   Insert "Basic Slot Robot" and its Reelsets/Paytable.

## 2. C3: Smart Game Engine
*   **Task 2.1:** Create `app/services/slot_math.py`.
    *   Logic to parse Reelset, Pick Symbols, Check Paylines.
*   **Task 2.2:** Update `app/routes/mock_provider.py`.
    *   Use `slot_math` instead of `Math.random()`.

## 3. C5: Admin UI
*   **Task 3.1:** Backend Router `app/routes/robots.py`.
*   **Task 3.2:** Frontend `RobotsPage.jsx`.

---

**Execution Start:** Immediate.
