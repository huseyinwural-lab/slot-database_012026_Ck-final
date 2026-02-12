# Provider Wallet Flow

**Model:** Seamless Wallet (Single Source of Truth)

## 1. Bet Placement Flow (Debit)
1.  **Request:** Provider sends `POST /bet` (Amount: 10.00).
2.  **Validation:** Adapter verifies signature.
3.  **Risk Guard:** Call `RiskService.check_bet_throttle(user_id)`.
    -   *Fail:* Return Provider-specific Error (e.g., "Internal Error" or "Limit Exceeded").
4.  **Wallet Lock:** `GameEngine` locks wallet row.
5.  **Balance Check:** `Available + Bonus >= Amount`.
6.  **Debit:** Deduct amount (Ledger: `game_bet`).
7.  **Response:** Success + New Balance.

## 2. Win Settlement Flow (Credit)
1.  **Request:** Provider sends `POST /win` (Amount: 50.00).
2.  **Idempotency:** Check `provider_event_id` in `GameEvent`.
    -   *Exists:* Return cached balance (No-op).
3.  **Credit:** Add amount (Ledger: `game_win`).
4.  **Response:** Success + New Balance.

## 3. Failure Scenarios
-   **Timeout:** If Internal DB is slow, Provider retries. Idempotency handles retry.
-   **Rollback:** Provider sends `POST /rollback`. We reverse the ledger entry referenced by `original_reference`.
