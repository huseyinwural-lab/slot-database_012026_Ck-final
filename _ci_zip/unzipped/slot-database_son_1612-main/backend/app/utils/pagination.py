from typing import Optional

from fastapi import Query

from app.models.common import PaginationParams


async def get_pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    include_total: bool = Query(False),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("desc"),
) -> PaginationParams:
    """Standard dependency for pagination & sorting params.

    Normalizes sort_dir and enforces common defaults across
    all list endpoints.
    """

    # Normalize sort_dir and whitelist
    normalized_dir = (sort_dir or "").lower().strip()
    if normalized_dir not in {"asc", "desc"}:
        normalized_dir = "desc"

    return PaginationParams(
        page=page,
        page_size=page_size,
        include_total=include_total,
        sort_by=sort_by,
        sort_dir=normalized_dir,
    )
