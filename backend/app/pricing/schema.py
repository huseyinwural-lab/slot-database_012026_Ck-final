from typing import Optional, Dict
from pydantic import BaseModel
from decimal import Decimal

class Quote(BaseModel):
    price: Decimal
    type: str
    duration: Optional[int] = None
    details: Dict = {}
