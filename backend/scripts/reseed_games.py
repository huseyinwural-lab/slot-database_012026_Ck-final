import asyncio
from app.core.database import db_wrapper
from app.routes.tenant import seed_default_tenants
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import random

async def main():
    db_wrapper.connect()
    db = db_wrapper.db
    
    print("🚀 Re-seeding Games for Testing...")
    
    # Get tenants
    tenants = await db.tenants.find({}, {"_id": 0, "id": 1}).to_list(100)
    tenant_ids = [t["id"] for t in tenants]
    
    if not tenant_ids:
        print("❌ No tenants found. Run seed_default_tenants first.")
        return

    # Seed Games
    game_types = [
        ("slot", "Mega Fortune Slot", "Evolution Gaming"),
        ("slot", "Book of Ra Deluxe", "Novomatic"),
        ("slot", "Starburst", "NetEnt"),
        ("roulette", "European Roulette", "Evolution Gaming"),
        ("blackjack", "Classic Blackjack", "Evolution Gaming")
    ]
    
    games_inserted = 0
    for tenant_id in tenant_ids:
        for game_type, name, provider in game_types:
            game = {
                "id": str(uuid4()),
                "name": name,
                "type": game_type,
                "provider": provider,
                "category": game_type, # Ensure category is set
                "tenant_id": tenant_id,
                "status": "active", # Ensure active
                "rtp": 96.5,
                "image_url": "https://placehold.co/300x200",
                "created_at": datetime.now(timezone.utc)
            }
            
            # Check existing by name and tenant
            existing = await db.games.find_one({"name": name, "tenant_id": tenant_id})
            if not existing:
                await db.games.insert_one(game)
                games_inserted += 1
            else:
                # Force update status to active for testing
                await db.games.update_one({"id": existing["id"]}, {"$set": {"status": "active", "category": game_type}})
                
    print(f"✅ Games seeded/updated: {games_inserted}")
    db_wrapper.close()

if __name__ == "__main__":
    asyncio.run(main())
