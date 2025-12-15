"""One-shot owner bootstrap for prod/staging.

Behavior:
- Runs ONLY if BOOTSTRAP_OWNER_EMAIL and BOOTSTRAP_OWNER_PASSWORD are provided.
- Creates an owner user ONLY if AdminUser table is empty.
- Idempotent: if there is already at least one AdminUser, it does nothing.

Used by scripts/start_prod.sh before starting uvicorn.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


async def main() -> None:
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlmodel import select

        from app.core.database import engine
        from app.models.sql_models import AdminUser, Tenant
        from app.utils.auth import get_password_hash

        email = os.environ.get("BOOTSTRAP_OWNER_EMAIL")
        password = os.environ.get("BOOTSTRAP_OWNER_PASSWORD")
        tenant_id = os.environ.get("BOOTSTRAP_OWNER_TENANT_ID", "default_casino")

        if not email or not password:
            print("[bootstrap_owner] SKIP: BOOTSTRAP_OWNER_EMAIL or BOOTSTRAP_OWNER_PASSWORD not set")
            return

        print(f"[bootstrap_owner] Found env for: {email}")

        async with AsyncSession(engine) as session:
            # Only if no admins exist
            res = await session.execute(select(AdminUser.id).limit(1))
            if res.scalar_one_or_none() is not None:
                print("[bootstrap_owner] SKIP: AdminUser table is not empty")
                return

            # Ensure tenant exists
            t_res = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = t_res.scalars().first()
            if tenant is None:
                print(f"[bootstrap_owner] Creating tenant: {tenant_id}")
                tenant = Tenant(id=tenant_id, name="Default Casino", type="owner", features={})
                session.add(tenant)
                await session.commit()

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
            print(f"[bootstrap_owner] CREATED: {email}")

    except Exception as e:
        print(f"[bootstrap_owner] FATAL ERROR: {e}")
        # Make sure we don't swallow errors, so the script fails and CI notices
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[bootstrap_owner] Uncaught exception: {e}")
        sys.exit(1)
