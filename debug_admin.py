#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app/backend')

from app.core.database import get_session, engine
from sqlmodel import select
from app.models.sql_models import AdminUser
from app.utils.auth import verify_password, get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession

async def debug_admin():
    print("🔍 Debugging admin user...")
    
    async with AsyncSession(engine) as session:
        # Check if admin exists
        stmt = select(AdminUser).where(AdminUser.email == 'admin@casino.com')
        result = await session.execute(stmt)
        admin = result.scalars().first()
        
        if not admin:
            print("❌ Admin user not found!")
            return
        
        print(f"✅ Admin found:")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   Status: {admin.status}")
        print(f"   Is Active: {admin.is_active}")
        print(f"   Password Hash: {admin.password_hash[:50]}...")
        print(f"   Tenant ID: {admin.tenant_id}")
        print(f"   Role: {admin.role}")
        print(f"   Is Platform Owner: {admin.is_platform_owner}")
        
        # Test password verification
        test_password = "Admin123!"
        print(f"\n🔐 Testing password verification with '{test_password}':")
        
        if admin.password_hash:
            is_valid = verify_password(test_password, admin.password_hash)
            print(f"   Password verification result: {is_valid}")
            
            # Test with a new hash
            new_hash = get_password_hash(test_password)
            print(f"   New hash: {new_hash[:50]}...")
            is_valid_new = verify_password(test_password, new_hash)
            print(f"   New hash verification: {is_valid_new}")
        else:
            print("   ❌ No password hash found!")

if __name__ == "__main__":
    asyncio.run(debug_admin())