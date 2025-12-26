# Seeding function adapted for SQL
async def seed_default_tenants(session: AsyncSession):
    # Check if default exists
    stmt = select(Tenant).where(Tenant.id == "default_casino")
    result = await session.execute(stmt)
    if result.scalars().first():
        return

    # Ensure demo_renter is also cleanly re-created if needed

    # Create Owner Tenant
    owner = Tenant(
        id="default_casino", 
        name="Default Casino", 
        type="owner",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_experiments": True,
            "can_use_kill_switch": True,
            "can_manage_affiliates": True,
            "can_use_crm": True,
            "can_use_game_robot": True,
            "can_manage_kyc": True,
            "can_manage_bonus": True,
        }
    )
    
    # Create Demo Renter
    renter = Tenant(
        id="demo_renter",
        name="Demo Renter",
        type="renter",
        features={
            "can_manage_admins": True,
            "can_view_reports": True,
            "can_manage_affiliates": False,
            "can_use_crm": False,
            "can_manage_experiments": False,
            "can_use_kill_switch": False,
            "can_use_game_robot": True,
            "can_manage_kyc": True,
            "can_manage_bonus": True,
        }
    )
    
    session.add(owner)
    session.add(renter)
    await session.commit()
    print("✅ SQL Tenants Seeded")
