# Sprint B Final: Security & E2E - Task Order

**Status:** ACTIVE
**Goal:** Harden the Game Loop (HMAC, Replay, Idempotency) and validate with strict E2E.

---

## 1. B-FIN-01: Callback Security (HMAC + Nonce)
*   **Task 1.1:** Update `CallbackSecurityMiddleware` in `app/middleware/callback_security.py`.
    *   Add Nonce Replay Check (using `CallbackNonce` table).
    *   Enforce Strict HMAC calculation (Raw Body).
*   **Task 1.2:** Create `CallbackNonce` Model in `app/models/game_models.py`.
*   **Task 1.3:** Register Model in Alembic & Migrate.

## 2. B-FIN-02: Idempotency (Event Level)
*   **Task 2.1:** Verify `GameEvent` constraints (already `unique=True`).
*   **Task 2.2:** Ensure `GameEngine` handles `IntegrityError` gracefully (return 200 OK + Balance).

## 3. B-FIN-03: Mock Provider Signing
*   **Task 3.1:** Update `mock_provider.py`.
    *   Generate `X-Callback-Timestamp`, `X-Callback-Nonce`, `X-Callback-Signature`.
    *   Use `adyen_hmac_key` (or provider specific secret) for signing.

## 4. B-FIN-04: E2E Testing
*   **Task 4.1:** Update `game-loop.spec.ts` to include signature validation checks (Happy Path).
*   **Task 4.2:** Create `backend/tests/test_callback_security.py` for Negative Paths (403, 409).

---

**Execution Start:** Immediate.
