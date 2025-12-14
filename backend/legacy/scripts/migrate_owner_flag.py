"""
Migration: Add is_platform_owner flag to existing admin users
Run once to set existing admin@casino.com as platform owner
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def migrate():
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    # Set admin@casino.com as platform owner
    result = await db.admins.update_one(
        {"email": "admin@casino.com"},
        {"$set": {"is_platform_owner": True}}
    )
    
    print(f"✅ Updated {result.modified_count} admin(s) to platform owner")
    
    # Set all other admins as non-owner (default)
    result2 = await db.admins.update_many(
        {"email": {"$ne": "admin@casino.com"}, "is_platform_owner": {"$exists": False}},
        {"$set": {"is_platform_owner": False}}
    )
    
    print(f"✅ Set is_platform_owner=False for {result2.modified_count} tenant admin(s)")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
