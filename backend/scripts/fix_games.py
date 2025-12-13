import asyncio
from app.core.database import db_wrapper

async def main():
    db_wrapper.connect()
    db = db_wrapper.db
    
    print("🚀 Fixing missing 'category' field in Games...")
    
    # Update games without category, set it to type or "slot"
    result = await db.games.update_many(
        {"category": {"$exists": False}},
        [{"$set": {"category": "$type"}}] # Use aggregation pipeline to copy 'type' to 'category'
    )
    
    print(f"✅ Updated {result.modified_count} games.")
    db_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main())
