from typing import Optional, Generic, List, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


class PaginationMeta(BaseModel):
    """Standard pagination metadata for list endpoints."""

    total: Optional[int] = None
    page: int
    page_size: int


class PaginationParams(BaseModel):
    """Incoming pagination and sorting parameters from query string."""

    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    include_total: bool = False
    sort_by: Optional[str] = None
    sort_dir: str = "desc"


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response wrapper.

    All list endpoints should return this shape so that
    OpenAPI schema is consistent and clients can rely
    on items/meta contract.
    """

    items: List[T]
    meta: PaginationMeta
