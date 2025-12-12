from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

from config import settings
from app.models.tenant import Tenant
from app.models.common import PaginatedResponse, PaginationParams, PaginationMeta
from app.utils.pagination import get_pagination_params

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


def get_db():
    client = AsyncIOMotorClient(settings.mongo_url)
    return client[settings.db_name]


@router.get("/", response_model=List[Tenant])
async def list_tenants() -> List[Tenant]:
    db = get_db()
    docs = await db.tenants.find({}, {"_id": 0}).to_list(100)
    return [Tenant(**d) for d in docs]


@router.post("/", response_model=Tenant)
async def create_tenant(tenant: Tenant = Body(...)) -> Tenant:
    db = get_db()
    # Basic uniqueness by name
    existing = await db.tenants.find_one({"name": tenant.name})
    if existing:
        raise HTTPException(status_code=400, detail="Tenant with this name already exists")

    tenant.created_at = datetime.now(timezone.utc)
    tenant.updated_at = tenant.created_at

    await db.tenants.insert_one(tenant.model_dump())
    return tenant


async def seed_default_tenants():
    db = get_db()
    count = await db.tenants.count_documents({})
    if count == 0:
        default_owner = Tenant(
            id="default_casino",
            name="Default Casino",
            type="owner",
            features={
                "can_use_game_robot": True,
                "can_edit_configs": True,
                "can_manage_bonus": True,
                "can_view_reports": True,
            },
        )
        demo_renter = Tenant(
            id="demo_renter",
            name="Demo Renter",
            type="renter",
            features={
                "can_use_game_robot": True,
                "can_edit_configs": False,
                "can_manage_bonus": True,
                "can_view_reports": True,
            },
        )
        await db.tenants.insert_many([
            default_owner.model_dump(),
            demo_renter.model_dump(),
        ])
