# Provider Adapter Contract (Draft)

## Overview
Standard interface for Game Providers (Simulator, Pragmatic, Evolution).

## Interface Definition (Proposed)
```python
class GameProviderAdapter(ABC):
    @abstractmethod
    async def launch_game(self, user: User, game_id: str, mode: str) -> str:
        """Returns game launch URL."""
        pass

    @abstractmethod
    async def process_callback(self, payload: dict) -> TransactionResult:
        """Handles webhook/callback from provider."""
        pass
        
    @abstractmethod
    async def get_balance(self, user: User) -> Decimal:
        """Syncs balance if needed."""
        pass
```

## Pragmatic Play Specifics
*Pending Documentation*
- Auth: Expects Token exchange?
- Callback: XML/JSON?
- Wallet: Seamless?

## Current Status
- **Simulator:** Implemented.
- **Pragmatic:** Pending API Docs.
