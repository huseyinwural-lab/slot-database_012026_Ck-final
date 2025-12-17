#!/usr/bin/env python3

import argparse
import json
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge audit events older than N days")
    parser.add_argument("--days", type=int, default=90)
    args = parser.parse_args()

    # Import inside main so the script can run from repo root
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

    from config import settings
    from sqlalchemy.ext.asyncio import create_async_engine

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in (settings.database_url or "") else {},
        future=True,
    )

    async def _run() -> int:
        async with engine.begin() as conn:
            # Table name is 'auditevent' for SQLite in this codebase.
            res = await conn.execute(
                text("DELETE FROM auditevent WHERE timestamp < :cutoff"),
                {"cutoff": cutoff},
            )
            deleted = res.rowcount or 0

        await engine.dispose()
        print(f"deleted={deleted} cutoff={cutoff.isoformat()}")
        return 0

    import asyncio

    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
