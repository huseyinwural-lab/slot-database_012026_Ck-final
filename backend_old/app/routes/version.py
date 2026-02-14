from fastapi import APIRouter

from app.core.build_info import get_build_info


router = APIRouter(prefix="/api", tags=["version"])


@router.get("/version")
async def version():
    # Public endpoint: returns only safe build metadata
    return get_build_info(service="backend")
