# Sprint C - Task 3: Admin UI (Robot Management) - Task Order

**Status:** ACTIVE
**Goal:** Expose the Math Engine controls to the Operations team via the Admin Panel.

---

## 1. Backend: Robots API
*   **Task 1.1:** Create `app/routes/robots.py`.
    *   `GET /`: List Robots (filters).
    *   `POST /{id}/toggle`: Activate/Deactivate.
    *   `POST /{id}/clone`: Clone config.
    *   `GET /math-assets`: List assets.
*   **Task 1.2:** Update `app/routes/games.py` (or new route).
    *   `GET /{game_id}/robot`: Get binding.
    *   `POST /{game_id}/robot`: Set binding.

## 2. Frontend: Robots Catalog
*   **Task 2.1:** Create `pages/RobotsPage.jsx`.
    *   Table: ID, Name, Config Summary, Actions.
    *   Drawer: JSON View of Config.
*   **Task 2.2:** Add to `Layout.jsx` sidebar (feature gated).

## 3. Frontend: Game Binding
*   **Task 3.1:** Update `pages/GameManagement.jsx` (or Detail).
    *   Add "Math Engine" Tab.
    *   Card showing current robot.
    *   Selector to bind new robot.

## 4. E2E: Admin Ops
*   **Task 4.1:** `e2e/tests/robot-admin-ops.spec.ts`.
    *   Clone Robot -> Bind to Game -> Spin -> Verify Robot ID.

---

**Execution Start:** Immediate.
