import asyncio
from sqlmodel import select
from app.core.database import async_session
from app.models.sql_models import AdminUser, Player, Transaction, Tenant
from app.utils.auth import create_access_token, get_password_hash
from app.services.wallet_ledger import apply_wallet_delta_with_ledger
from datetime import timedelta
import uuid

async def setup():
    async with async_session() as session:
        # 1. Ensure Tenant
        stmt = select(Tenant).where(Tenant.id == "default_casino")
        tenant = (await session.execute(stmt)).scalars().first()
        if not tenant:
            tenant = Tenant(id="default_casino", name="Default Casino")
            session.add(tenant)
            await session.commit()

        # 2. Ensure Admin
        stmt = select(AdminUser).where(AdminUser.email == "admin@casino.com")
        admin = (await session.execute(stmt)).scalars().first()
        if not admin:
            admin = AdminUser(
                email="admin@casino.com",
                username="superadmin",
                full_name="Super Owner",
                role="Super Admin",
                tenant_id="default_casino",
                is_platform_owner=True,
                password_hash=get_password_hash("Admin123!"),
                status="active"
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
        
        # 3. Create Admin Token
        admin_token = create_access_token(
            data={"sub": admin.id, "email": admin.email, "tenant_id": admin.tenant_id, "role": admin.role},
            expires_delta=timedelta(days=1)
        )

        # 4. Ensure Player
        stmt = select(Player).where(Player.email == "player@smoke.test")
        player = (await session.execute(stmt)).scalars().first()
        if not player:
            player = Player(
                email="player@smoke.test",
                username="smoketest",
                tenant_id="default_casino",
                password_hash=get_password_hash("Player123!"),
                kyc_status="verified"
            )
            session.add(player)
            await session.commit()
            await session.refresh(player)

        # 5. Create Completed Deposit (for Refund & Adyen Replay)
        dep_tx_id = str(uuid.uuid4())
        dep_tx = Transaction(
            id=dep_tx_id,
            tenant_id="default_casino",
            player_id=player.id,
            type="deposit",
            amount=100.0,
            currency="USD",
            status="completed",
            state="completed",
            provider="adyen",
            provider_event_id=f"evt_{dep_tx_id}", # Used for replay check logic
            method="adyen_payment_link"
        )
        session.add(dep_tx)
        
        # Apply ledger so refund has funds
        await apply_wallet_delta_with_ledger(
            session,
            tenant_id="default_casino",
            player_id=player.id,
            tx_id=dep_tx_id,
            event_type="deposit_succeeded",
            delta_available=100.0,
            delta_held=0.0,
            currency="USD",
            idempotency_key=f"setup:{dep_tx_id}",
            provider="adyen",
            provider_ref=f"evt_{dep_tx_id}",
            provider_event_id=f"evt_{dep_tx_id}"
        )
        await session.commit()

        # 6. Create Pending Withdrawal (for Payout)
        wd_tx_id = str(uuid.uuid4())
        wd_tx = Transaction(
            id=wd_tx_id,
            tenant_id="default_casino",
            player_id=player.id,
            type="withdrawal",
            amount=50.0,
            currency="USD",
            status="pending",
            state="approved",
            provider="mock_psp"
        )
        session.add(wd_tx)
        await session.commit()

        print(f"ADMIN_TOKEN={admin_token}")
        print(f"DEPOSIT_TX_ID={dep_tx_id}")
        print(f"WITHDRAWAL_TX_ID={wd_tx_id}")

if __name__ == "__main__":
    asyncio.run(setup())
