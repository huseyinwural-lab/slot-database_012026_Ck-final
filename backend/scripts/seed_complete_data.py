"""
Complete data seeding for production-ready platform
- Default tenants
- Demo games
- Demo transactions
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import random
from config import settings


async def seed_all():
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    print("🚀 Starting complete data seeding...")
    
    # 1. Seed Tenants
    print("\n📦 Seeding tenants...")
    
    tenants = [
        {
            "id": "default_casino",
            "name": "Default Casino (Owner)",
            "type": "owner",
            "can_use_game_robot": True,
            "can_edit_configs": True,
            "can_manage_bonus": True,
            "can_view_reports": True,
            "can_manage_admins": True,
            "can_manage_kyc": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid4()),
            "name": "Demo Renter Casino",
            "type": "renter",
            "can_use_game_robot": False,
            "can_edit_configs": False,
            "can_manage_bonus": True,
            "can_view_reports": True,
            "can_manage_admins": False,
            "can_manage_kyc": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid4()),
            "name": "VIP Casino Operator",
            "type": "renter",
            "can_use_game_robot": True,
            "can_edit_configs": False,
            "can_manage_bonus": True,
            "can_view_reports": True,
            "can_manage_admins": True,
            "can_manage_kyc": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
    ]
    
    for tenant in tenants:
        existing = await db.tenants.find_one({"id": tenant["id"]})
        if not existing:
            await db.tenants.insert_one(tenant)
            print(f"  ✅ Created tenant: {tenant['name']}")
        else:
            print(f"  ⚠️  Tenant already exists: {tenant['name']}")
    
    tenant_ids = [t["id"] for t in tenants]
    
    # 2. Seed Games
    print("\n🎮 Seeding demo games...")
    
    game_types = [
        ("slot", "Mega Fortune Slot", "Evolution Gaming", "EN"),
        ("slot", "Book of Ra Deluxe", "Novomatic", "EN"),
        ("slot", "Starburst", "NetEnt", "EN"),
        ("roulette", "European Roulette", "Evolution Gaming", "EN"),
        ("roulette", "Lightning Roulette", "Evolution Gaming", "EN"),
        ("blackjack", "Classic Blackjack", "Evolution Gaming", "EN"),
        ("blackjack", "Speed Blackjack", "Pragmatic Play", "EN"),
        ("poker", "Texas Hold'em", "PokerStars", "EN"),
        ("slot", "Wolf Gold", "Pragmatic Play", "EN"),
        ("slot", "Sweet Bonanza", "Pragmatic Play", "EN"),
        ("baccarat", "Live Baccarat", "Evolution Gaming", "EN"),
        ("slot", "Dead or Alive 2", "NetEnt", "EN"),
        ("slot", "Gonzo's Quest", "NetEnt", "EN"),
        ("roulette", "American Roulette", "Microgaming", "EN"),
        ("slot", "Reactoonz", "Play'n GO", "EN")
    ]
    
    games_inserted = []
    for tenant_id in tenant_ids:
        for game_type, name, provider, lang in game_types:
            game_id = str(uuid4())
            game = {
                "id": game_id,
                "name": name,
                "type": game_type,
                "provider": provider,
                "language": lang,
                "tenant_id": tenant_id,
                "status": "active",
                "rtp": round(random.uniform(94.0, 98.5), 2),
                "min_bet": random.choice([0.1, 0.5, 1.0, 2.0]),
                "max_bet": random.choice([100, 250, 500, 1000]),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            existing = await db.games.find_one({"name": name, "tenant_id": tenant_id})
            if not existing:
                await db.games.insert_one(game)
                games_inserted.append(game_id)
    
    print(f"  ✅ Created {len(games_inserted)} games across {len(tenant_ids)} tenants")
    
    # 3. Seed Transactions
    print("\n💰 Seeding demo transactions...")
    
    transaction_count = 0
    
    for tenant_id in tenant_ids:
        # Get games for this tenant
        tenant_games = await db.games.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1}).to_list(100)
        if not tenant_games:
            continue
        
        game_ids = [g["id"] for g in tenant_games]
        
        # Generate 30-50 transactions per tenant over last 30 days
        num_transactions = random.randint(30, 50)
        
        for _ in range(num_transactions):
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            transaction_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            # Bet transaction
            bet_amount = round(random.uniform(1, 100), 2)
            bet_transaction = {
                "id": str(uuid4()),
                "player_id": str(uuid4()),  # Random player
                "game_id": random.choice(game_ids),
                "tenant_id": tenant_id,
                "type": "bet",
                "amount": bet_amount,
                "status": "completed",
                "created_at": transaction_date,
                "currency": "USD"
            }
            await db.transactions.insert_one(bet_transaction)
            transaction_count += 1
            
            # Win transaction (RTP ~95%)
            if random.random() < 0.95:  # 95% of bets have a win (but lower amount)
                win_amount = round(bet_amount * random.uniform(0.3, 1.8), 2)
                win_transaction = {
                    "id": str(uuid4()),
                    "player_id": bet_transaction["player_id"],
                    "game_id": bet_transaction["game_id"],
                    "tenant_id": tenant_id,
                    "type": "win",
                    "amount": win_amount,
                    "status": "completed",
                    "created_at": transaction_date + timedelta(seconds=5),
                    "currency": "USD"
                }
                await db.transactions.insert_one(win_transaction)
                transaction_count += 1
    
    print(f"  ✅ Created {transaction_count} transactions")
    
    # 4. Summary
    print("\n" + "="*60)
    print("✅ SEEDING COMPLETE!")
    print("="*60)
    print(f"📦 Tenants: {len(tenant_ids)}")
    print(f"🎮 Games: {len(games_inserted)}")
    print(f"💰 Transactions: {transaction_count}")
    print("\n🎯 Ready for testing!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_all())
