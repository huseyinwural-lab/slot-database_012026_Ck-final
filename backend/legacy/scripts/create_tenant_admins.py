"""
Create admin users for each tenant for testing
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from uuid import uuid4
from config import settings
from app.utils.auth import get_password_hash


async def create_admins():
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.db_name]
    
    print("👥 Creating tenant admin users...")
    
    # Get all tenants except default (owner already has admin)
    tenants = await db.tenants.find({"type": "renter"}, {"_id": 0}).to_list(100)
    
    for tenant in tenants:
        tenant_id = tenant["id"]
        tenant_name = tenant["name"]
        
        # Create admin email based on tenant name
        email = f"admin-{tenant_id[:8]}@tenant.com"
        
        # Check if admin already exists
        existing = await db.admins.find_one({"email": email})
        if existing:
            print(f"  ⚠️  Admin already exists for {tenant_name}: {email}")
            continue
        
        # Create admin user
        password = "TenantAdmin123!"  # Demo password
        password_hash = get_password_hash(password)
        
        admin = {
            "id": str(uuid4()),
            "username": email.split("@")[0],
            "email": email,
            "full_name": f"{tenant_name} Admin",
            "role": "Tenant Admin",
            "tenant_id": tenant_id,
            "is_platform_owner": False,  # IMPORTANT: Not an owner
            "department": "Operations",
            "status": "active",
            "is_2fa_enabled": False,
            "password_hash": password_hash,
            "allowed_modules": [],
            "created_at": datetime.utcnow(),
            "last_login": None,
            "last_ip": None
        }
        
        await db.admins.insert_one(admin)
        print(f"  ✅ Created admin for {tenant_name}")
        print(f"     Email: {email}")
        print(f"     Password: {password}")
    
    print("\n" + "="*60)
    print("✅ TENANT ADMINS CREATED!")
    print("="*60)
    print("\n📝 Login Credentials:")
    print("\n🏢 OWNER (Platform Admin):")
    print("   Email: admin@casino.com")
    print("   Password: Admin123!")
    
    print("\n🏪 TENANT ADMINS:")
    tenant_admins = await db.admins.find(
        {"is_platform_owner": False}, 
        {"_id": 0, "email": 1, "full_name": 1, "tenant_id": 1}
    ).to_list(100)
    
    for admin in tenant_admins:
        tenant = await db.tenants.find_one({"id": admin["tenant_id"]}, {"_id": 0, "name": 1})
        print(f"\n   {tenant['name'] if tenant else 'Unknown'}:")
        print(f"   Email: {admin['email']}")
        print(f"   Password: TenantAdmin123!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_admins())
