import asyncio
from app.core.database import db_wrapper
from app.routes.tenant import seed_default_tenants

async def main():
    db_wrapper.connect()
    await seed_default_tenants()
    print("Force seed complete.")
    db_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main())
