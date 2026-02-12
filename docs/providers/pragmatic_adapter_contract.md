# Pragmatic Play Adapter Contract (Faz 6A)

**Status:** DRAFT (Waiting for Official Docs)
**Version:** 0.1

## 1. Integration Scope
- **Seamless Wallet:** Single balance source (Our `Player` / `WalletBalance` tables).
- **Protocol:** HTTP JSON / XML (Assumed based on industry standard).

## 2. Adapter Interface
```python
class PragmaticAdapter(BaseProviderAdapter):
    """
    Standard interface for Pragmatic Play integration.
    Handles Game Launch and Callback processing.
    """
    
    PROVIDER_ID = "pragmatic"

    async def launch_game(self, user: User, game_id: str, mode: str = "real") -> str:
        """
        Generates the specialized launch URL signed with our casino key.
        Steps:
        1. Create Session/Token in our DB.
        2. Construct Provider URL with `token` and `symbol`.
        3. Return URL.
        """
        pass

    async def handle_callback(self, payload: dict, signature: str) -> dict:
        """
        Main entry point for 'Authenticate', 'Balance', 'Bet', 'Win'.
        
        Mandatory Checks:
        - Signature Validation (HMAC)
        - Idempotency (Provider Ref)
        - Wallet Invariants (Sufficient Funds)
        """
        pass
```

## 3. Key Callback Methods (Expected)
| Method | Description | Our Action |
|--------|-------------|------------|
| `authenticate` | Validate token from launch. | Return UserID, Currency, Balance. |
| `balance` | Check current funds. | Query `WalletBalance`. |
| `bet` | Place a wager. | `wallet_ledger.spend(..., amount)`. |
| `result` | Win/Loss settlement. | `wallet_ledger.add(..., amount)`. |
| `rollback` | Void a previous transaction. | Reverse ledger entry. |

## 4. Next Steps
- Receive API Docs.
- Map exact JSON fields to `Transaction` model.
- Implement `PragmaticAdapter` class.
