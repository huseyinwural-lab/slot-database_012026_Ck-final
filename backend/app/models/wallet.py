from typing import Any, Dict, Optional

from pydantic import BaseModel


class TransactionOut(BaseModel):
    id: str
    type: str
    amount: float
    currency: str
    state: str
    status: str
    idempotency_key: Optional[str] = None
    provider: Optional[str] = None
    provider_event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WalletTxResponse(BaseModel):
    transaction: TransactionOut
