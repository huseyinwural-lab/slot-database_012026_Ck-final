from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    type: str
    amount: float
    currency: str
    state: str
    status: str
    idempotency_key: Optional[str] = None
    provider: Optional[str] = None
    provider_event_id: Optional[str] = None

    # ORM attribute is metadata_json, response key will be "metadata"
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        serialization_alias="metadata",
    )


class WalletTxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction: TransactionOut
