# Sprint B (Part 2): Frontend & Security - Task Order

**Status:** ACTIVE
**Goal:** Build the visible Casino (Catalog, Window) and secure the invisible Engine.

---

## 1. P0-Frontend: Catalog & Window
*   **Task 1.1:** Create `GameCatalog.jsx` (List & Search).
    *   API: `GET /api/v1/games`.
*   **Task 1.2:** Create `GameRoom.jsx` (The Play Window).
    *   API: `POST /api/v1/games/launch`.
    *   Component: `MockGameFrame` (Simulates iframe/game client).
    *   Logic: Calls `mock-provider/spin` -> Updates Balance.

## 2. P0-Security: Callback Gate
*   **Task 2.1:** Implement `CallbackSecurityMiddleware` (or dependency).
    *   Check `X-Signature` (HMAC).
    *   Check `X-Timestamp` (Replay).
    *   Validate IP (Allowlist).

## 3. P0-E2E: Full Simulation
*   **Task 3.1:** Write `e2e/tests/game-loop.spec.ts`.
    *   Login -> Open Catalog -> Launch Game -> Spin -> Verify Balance.

---

**Execution Start:** Immediate.
