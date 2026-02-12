# Faz 6A: Provider Integration Plan (Pragmatic Play)

**Status:** DRAFT
**Prerequisite:** API Documentation

## 1. Architecture: Adapter Pattern
We will implement a `PragmaticAdapter` that adheres to the `GameProvider` interface.

```python
class PragmaticAdapter(GameProvider):
    async def launch_game(self, ...): ...
    async def handle_callback(self, ...): ...
    async def validate_signature(self, ...): ...
```

## 2. Wallet Synchronization Strategy
- **Seamless Wallet:** We act as the single source of truth.
- **Flow:**
    1.  Provider sends `bet` request.
    2.  We lock wallet -> Check Funds -> Debit -> Risk Check.
    3.  Respond `OK` + New Balance.
    4.  If Risk Fail -> Respond `Error` (Provider handles retry/display).

## 3. Callback Validation Flow
1.  **Authentication:** Validate Hash/Signature in Header.
2.  **Idempotency:** Check `provider_tx_id` in `GameEvent` table.
3.  **Session:** Verify `player_id` and `game_id` match active session.

## 4. Fraud Surface Analysis
- **Round Scumming:** Player delays "Win" callback? (Server-to-server prevents this mostly).
- **Bonus Abuse:** Buying bonuses within game using real money.
    -   *Mitigation:* Map game-internal events to our Ledger types if possible.

## 5. Interface Contract
Pending official docs, but standardizing on:
- `user_id`: Our internal UUID.
- `currency`: ISO code (USD/EUR).
- `amount`: Float (2 decimals).
