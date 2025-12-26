# Sprint B (Part 3): Player Game Experience & E2E - Task Order

**Status:** ACTIVE
**Goal:** Deliver the visible "Casino Loop" (Catalog -> Play -> Result) and prove it with rigorous E2E testing.

---

## 1. B2: Player Frontend & Launch API (P0)
**Goal:** Player can select and play a game.

*   **Task 1.1:** Backend - `GameSession` & Launch Logic.
    *   Endpoint: `POST /api/v1/games/launch`.
    *   Logic: Validate Game -> Create Session -> Return Launch URL/Token.
*   **Task 1.2:** Frontend - `GameCatalog.jsx`.
    *   UI: Grid of games, Search bar.
    *   Integration: Calls `GET /api/v1/games`.
*   **Task 1.3:** Frontend - `GameRoom.jsx` (Mock Window).
    *   UI: Iframe container (simulated), Balance display, Spin button.
    *   Integration: Calls `POST /api/v1/mock-provider/spin` (simulating client-side game logic calling provider).
*   **Task 1.4:** Frontend - `GameHistory.jsx`.
    *   UI: List of recent spins/wins.

## 2. B6: Callback Security Gate (P0)
**Goal:** Secure the "Game Engine" from forged webhooks.

*   **Task 2.1:** Implement `CallbackSecurityMiddleware`.
    *   Verify `X-Signature` (HMAC-SHA256).
    *   Verify `X-Timestamp` (Replay protection).
    *   Apply to `/api/v1/integrations/callback`.

## 3. B5: E2E Full Simulation (P0)
**Goal:** Verify the entire loop end-to-end.

*   **Task 3.1:** `e2e/tests/casino-game-loop.spec.ts`.
    *   Flow: Login -> Select Game -> Spin -> Verify Wallet Update.
    *   Negative: Insufficient funds, Invalid Signature.

---

**Execution Start:** Immediate.
