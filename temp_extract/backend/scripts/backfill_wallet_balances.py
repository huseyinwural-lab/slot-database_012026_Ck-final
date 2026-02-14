import argparse
import asyncio
import logging
from typing import Optional

from sqlmodel import select

from app.core.database import async_session
from app.models.sql_models import Player
from app.repositories.ledger_repo import WalletBalance

logger = logging.getLogger(__name__)


async def _backfill_wallet_balances(
    *,
    tenant_id: Optional[str],
    batch_size: int,
    dry_run: bool,
    force: bool,
    session_factory=None,
) -> None:
    """Backfill WalletBalance rows from Player aggregates.

    Mapping:
    - Player.balance_real_available -> WalletBalance.balance_real_available
    - Player.balance_real_held      -> WalletBalance.balance_real_pending

    Idempotency:
    - Default: if WalletBalance exists, skip.
    - With --force: overwrite existing balances.
    """

    scanned_players = 0
    created = 0
    skipped_exists = 0
    updated_forced = 0
    errors = 0

    factory = session_factory or async_session

    async with factory() as session:
        offset = 0
        while True:
            stmt = select(Player)
            if tenant_id:
                stmt = stmt.where(Player.tenant_id == tenant_id)
            stmt = stmt.offset(offset).limit(batch_size)

            result = await session.execute(stmt)
            players = result.scalars().all()
            if not players:
                break

            for p in players:
                scanned_players += 1
                try:
                    wb_stmt = select(WalletBalance).where(
                        WalletBalance.tenant_id == p.tenant_id,
                        WalletBalance.player_id == p.id,
                        WalletBalance.currency == "USD",
                    )
                    wb_res = await session.execute(wb_stmt)
                    wb = wb_res.scalars().first()

                    target_available = float(p.balance_real_available)
                    target_pending = float(p.balance_real_held)

                    if wb is None:
                        if dry_run:
                            created += 1
                            continue

                        wb = WalletBalance(
                            tenant_id=p.tenant_id,
                            player_id=p.id,
                            currency="USD",
                            balance_real_available=target_available,
                            balance_real_pending=target_pending,
                        )
                        session.add(wb)
                        created += 1
                    else:
                        if not force:
                            skipped_exists += 1
                            continue

                        if dry_run:
                            updated_forced += 1
                            continue

                        wb.balance_real_available = target_available
                        wb.balance_real_pending = target_pending
                        updated_forced += 1

                except Exception as exc:  # pragma: no cover - defensive
                    errors += 1
                    logger.error(
                        "Error processing player %s (tenant=%s): %s",
                        p.id,
                        p.tenant_id,
                        exc,
                    )

            if not dry_run:
                await session.commit()

            offset += batch_size

    logger.info(
        "Backfill summary | scanned=%s created=%s skipped_exists=%s updated_forced=%s errors=%s",
        scanned_players,
        created,
        skipped_exists,
        updated_forced,
        errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill WalletBalance from Player aggregates")
    parser.add_argument("--tenant-id", dest="tenant_id", help="Limit backfill to a single tenant_id", default=None)
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=1000)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--force", dest="force", action="store_true")

    args = parser.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be a positive integer")

    asyncio.run(
        _backfill_wallet_balances(
            tenant_id=args.tenant_id,
            batch_size=args.batch_size,
            dry_run=bool(args.dry_run),
            force=bool(args.force),
        )
    )


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
