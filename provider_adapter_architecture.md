# Provider Adapter Architecture

**Pattern:** Adapter / Bridge
**Goal:** Decouple external provider protocols from internal Game Engine logic.

## 1. Core Interface
We define a base abstract class `BaseProvider` that all providers must implement.

```python
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier (e.g., 'pragmatic')"""
        pass

    @abstractmethod
    async def validate_request(self, request: Request) -> bool:
        """Validates IP, Signature, etc."""
        pass

    @abstractmethod
    async def handle_bet(self, payload: dict) -> dict:
        """Process debit request. Returns provider-formatted response."""
        pass

    @abstractmethod
    async def handle_win(self, payload: dict) -> dict:
        """Process credit request. Returns provider-formatted response."""
        pass
```

## 2. Data Mapping Strategy
| Pragmatic Field | Internal Model | Notes |
|-----------------|----------------|-------|
| `userId` | `Player.id` | Must be valid UUID. |
| `roundId` | `GameRound.provider_round_id` | Scope of aggregation. |
| `reference` | `GameEvent.provider_event_id` | **Idempotency Key**. |
| `amount` | `GameEvent.amount` | |
| `gameId` | `Game.external_id` | |

## 3. Routing
- **Endpoint:** `POST /api/v1/games/callback/{provider_id}`
- **Dispatcher:** `GamesCallbackRouter` looks up Adapter by `provider_id`.
