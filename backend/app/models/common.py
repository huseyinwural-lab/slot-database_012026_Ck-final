from pydantic import BaseModel
from typing import Optional


class PaginationMeta(BaseModel):
    """Standard pagination metadata for list endpoints."""

    total: Optional[int] = None
    page: int
    page_size: int
