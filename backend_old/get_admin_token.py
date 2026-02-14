import asyncio
from app.core.database import async_session
from app.models.sql_models import AdminUser
from app.utils.auth import create_access_token
from datetime import timedelta
from sqlmodel import select

async def get_token():
    async with async_session() as session:
        stmt = select(AdminUser).where(AdminUser.email == "admin@casino.com")
        admin = (await session.execute(stmt)).scalars().first()
        if not admin:
            # Create if needed (reuse seed logic?)
            # Just print error
            print("Admin not found")
            return
        
        token = create_access_token(
            data={"sub": admin.id, "email": admin.email, "tenant_id": admin.tenant_id, "role": admin.role},
            expires_delta=timedelta(days=1)
        )
        print(token)

if __name__ == "__main__":
    asyncio.run(get_token())
