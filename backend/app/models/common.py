from typing import Optional, Generic, List, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


class PaginationMeta(BaseModel):
    """Standard pagination metadata for list endpoints."""

    total: Optional[int] = None
    page: int
    page_size: int


T = TypeVar("T")


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated response wrapper.

    All list endpoints should return this shape so that
    OpenAPI schema is consistent and clients can rely
    on items/meta contract.
    """

    items: List[T]
    meta: PaginationMeta
