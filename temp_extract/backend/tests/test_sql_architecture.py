import asyncio
import sys
import os

# Set path manually
sys.path.append(os.path.abspath("/app/backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from app.models.sql_models import Tenant, AdminUser

# Test with SQLite to verify ORM logic without running Postgres container
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def test_sql_logic():
    print("🚀 Starting SQL Logic Smoke Test...")
    
    # 1. Init DB Engine
    try:
        engine = create_async_engine(TEST_DB_URL, echo=False)
    except Exception as e:
        print(f"Error creating engine: {e}")
        return

    # 2. Create Tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        print("   ✅ Tables Created (Schema Valid)")
    except Exception as e:
        print(f"   ❌ Schema Error: {e}")
        # Print detailed error for debugging imports/models
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. Session & Data Operations
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Create Tenant
            tenant = Tenant(name="Test Casino", type="owner", features={"robot": True})
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            print(f"   ✅ Tenant Created: {tenant.name} (ID: {tenant.id})")
            
            # Create Admin
            admin = AdminUser(
                email="admin@test.com",
                username="admin",
                full_name="Super Admin",
                password_hash="secret_hash",
                role="Super Admin",
                tenant_id=tenant.id
            )
            session.add(admin)
            await session.commit()
            
            # Verify Relationship & Fetch
            stmt = select(AdminUser).where(AdminUser.email == "admin@test.com")
            result = await session.exec(stmt)
            fetched_admin = result.first()
            
            if fetched_admin and fetched_admin.tenant_id == tenant.id:
                print(f"   ✅ Admin Fetched & Linked Correctly: {fetched_admin.email}")
            else:
                print("   ❌ Admin Fetch Failed or Link Broken")
                sys.exit(1)
    except Exception as e:
        print(f"Session Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n✨ SQL ARCHITECTURE VERIFIED ✨")

if __name__ == "__main__":
    asyncio.run(test_sql_logic())
