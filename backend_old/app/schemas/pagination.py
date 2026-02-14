from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class PaginationMetaPublic(BaseModel):
    total: Optional[int] = None
    page: int
    page_size: int


class PaginatedResponsePublic(BaseModel, Generic[T]):
    items: List[T]
    meta: PaginationMetaPublic
