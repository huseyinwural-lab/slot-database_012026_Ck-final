"""One-shot owner bootstrap for prod/staging/dev.

Behavior:
- Runs only if BOOTSTRAP_ENABLED=true.
- Creates DB Tables if missing (SQLite).
- Creates an owner user if AdminUser table is empty.
- Requires BOOTSTRAP_OWNER_EMAIL and BOOTSTRAP_OWNER_PASSWORD.
- Updates default tenant features to ensure all modules are accessible.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

if os.getenv("BOOTSTRAP_ENABLED", "").lower() != "true":
    print("[bootstrap_owner] BOOTSTRAP_ENABLED!=true, skipping.")
    sys.exit(0)


sys.path.append(str(Path(__file__).resolve().parents[1]))

# Default features for the Platform Owner Tenant
DEFAULT_OWNER_FEATURES = {
    "can_manage_admins": True,
    "can_view_reports": True,
    "can_manage_experiments": True,
    "can_use_kill_switch": True,
    "can_manage_affiliates": True,
    "can_use_crm": True,
    "can_use_game_robot": True,
    "can_manage_finance": True,
    "can_edit_configs": True,
    "can_manage_bonus": True,
    "can_manage_kyc": True,
}

# Default features for the Demo Renter tenant used in E2E tenant gating tests
DEFAULT_DEMO_RENTER_FEATURES = {
    "can_manage_admins": True,
    "can_view_reports": True,
    "can_manage_experiments": False,
    "can_use_kill_switch": False,
    "can_manage_affiliates": False,
    "can_use_crm": False,
    "can_use_game_robot": True,
    "can_manage_finance": False,
    "can_edit_configs": False,
    "can_manage_bonus": True,
    "can_manage_kyc": False,
}


async def main() -> None:
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlmodel import select, SQLModel

        from app.core.database import engine
        # Ensure all models are registered before SQLModel relationships are configured.
        # (Fixes: Tenant.games Relationship referencing "Game")
        from app.models import game_models  # noqa: F401
        from app.models.sql_models import AdminUser, Tenant
        from app.utils.auth import get_password_hash

        # Initialize Tables if SQLite (auto-fix for "no such table" error)
        if "sqlite" in str(engine.url):
            print("[bootstrap_owner] SQLite detected. Ensuring tables exist...")
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)

        email = os.environ.get("BOOTSTRAP_OWNER_EMAIL")
        password = os.environ.get("BOOTSTRAP_OWNER_PASSWORD")
        tenant_id = os.environ.get("BOOTSTRAP_OWNER_TENANT_ID", "default_casino")

        if not email or not password:
            print("[bootstrap_owner] FATAL: Missing BOOTSTRAP_OWNER_EMAIL or BOOTSTRAP_OWNER_PASSWORD while BOOTSTRAP_ENABLED=true")
            sys.exit(1)
        
        async with AsyncSession(engine) as session:
            # 1. Ensure Tenant Exists & Has Correct Features
            t_res = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = t_res.scalars().first()
            
            if tenant is None:
                print(f"[bootstrap_owner] Creating tenant: {tenant_id}")
                tenant = Tenant(
                    id=tenant_id, 
                    name="Default Casino", 
                    type="owner", 
                    features=DEFAULT_OWNER_FEATURES
                )
                session.add(tenant)
                await session.commit()
            else:
                # Update features if they are empty or missing
                current_features = tenant.features or {}
                needs_update = False
                for k, v in DEFAULT_OWNER_FEATURES.items():
                    if k not in current_features:
                        current_features[k] = v
                        needs_update = True
                
                if needs_update:
                    print(f"[bootstrap_owner] Updating features for tenant {tenant_id}...")
                    tenant.features = current_features
                    session.add(tenant)
                    await session.commit()


            # 1b. Ensure demo_renter tenant exists for E2E gating matrix
            demo_id = "demo_renter"
            demo_res = await session.execute(select(Tenant).where(Tenant.id == demo_id))
            demo_tenant = demo_res.scalars().first()
            if demo_tenant is None:
                print(f"[bootstrap_owner] Creating tenant: {demo_id}")
                demo_tenant = Tenant(
                    id=demo_id,
                    name="Demo Renter",
                    type="renter",
                    features=DEFAULT_DEMO_RENTER_FEATURES,
                )
                session.add(demo_tenant)
                await session.commit()

            # 2. Ensure Owner User Exists
            res = await session.execute(select(AdminUser.id).where(AdminUser.email == email))
            existing_user = res.scalars().first()
            
            if existing_user is None:
                print(f"[bootstrap_owner] Creating platform owner: {email}")
                owner = AdminUser(
                    tenant_id=tenant_id,
                    username=email.split("@")[0],
                    email=email,
                    full_name="Platform Owner",
                    password_hash=get_password_hash(password),
                    role="platform_owner",
                    tenant_role="platform_owner",
                    is_platform_owner=True,
                    status="active",
                    is_active=True,
                    failed_login_attempts=0,
                )
                session.add(owner)
                await session.commit()
                print(f"[bootstrap_owner] SUCCESS: Created user {email}")
            else:
                print(f"[bootstrap_owner] User {email} already exists. Skipping creation.")

    except Exception as e:
        print(f"[bootstrap_owner] FATAL ERROR: {e}")
        # Don't crash container
        sys.exit(0)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[bootstrap_owner] Uncaught exception: {e}")
        sys.exit(1)
