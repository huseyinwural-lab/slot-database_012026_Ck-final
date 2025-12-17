#!/usr/bin/env python3

import argparse
import json
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge audit events older than N days")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true", help="Report how many rows would be deleted and exit")
    parser.add_argument("--batch-size", type=int, default=5000, help="Delete in batches to reduce lock risk")
    args = parser.parse_args()

    # Import inside main so the script can run from repo root
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

    from config import settings
    from sqlalchemy.ext.asyncio import create_async_engine

    # Cutoff is always computed in UTC.
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in (settings.database_url or "") else {},
        future=True,
    )

    async def _run() -> int:
        start = time.perf_counter()

        deleted_total = 0

        async with engine.begin() as conn:
            # Table name is 'auditevent' in this codebase.
            # The script connects to whatever DB is configured via settings.database_url
            # (SQLite in dev; Postgres in staging/prod).
            count = (
                await conn.execute(
                    text("SELECT COUNT(*) FROM auditevent WHERE timestamp < :cutoff"),
                    {"cutoff": cutoff},
                )
            ).scalar_one()

            if args.dry_run:
                duration_ms = int((time.perf_counter() - start) * 1000)
                print(
                    json.dumps(
                        {
                            "event": "audit.purge",
                            "dry_run": True,
                            "days": args.days,
                            "batch_size": args.batch_size,
                            "cutoff_ts": cutoff.isoformat(),
                            "to_delete": int(count),
                            "deleted_count": 0,
                            "duration_ms": duration_ms,
                        },
                        ensure_ascii=False,
                    )
                )
                await engine.dispose()
                return 0

            # Batch delete to reduce lock risk on large tables
            while True:
                res = await conn.execute(
                    text(
                        "DELETE FROM auditevent WHERE id IN (SELECT id FROM auditevent WHERE timestamp < :cutoff LIMIT :batch_size)"
                    ),
                    {"cutoff": cutoff, "batch_size": args.batch_size},
                )
                batch_deleted = res.rowcount or 0
                deleted_total += batch_deleted

                if batch_deleted == 0:
                    break

        await engine.dispose()

        duration_ms = int((time.perf_counter() - start) * 1000)
        print(
            json.dumps(
                {
                    "event": "audit.purge",
                    "dry_run": False,
                    "days": args.days,
                    "batch_size": args.batch_size,
                    "cutoff_ts": cutoff.isoformat(),
                    "deleted_count": int(deleted_total),
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
            )
        )

        return 0

    import asyncio

    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
