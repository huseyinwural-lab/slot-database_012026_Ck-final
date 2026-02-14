import os
import sys
import asyncio


sys.path.append(os.path.abspath("/app/backend"))

from server import app  # noqa: F401
from app.models.reconciliation import (
    create_finding,
    list_findings,
    resolve_finding,
)


def test_reconciliation_create_and_list(async_session_factory):
    async def _run():
        async with async_session_factory() as session:
            finding = await create_finding(
                session,
                provider="mockpsp",
                tenant_id="t1",
                player_id="p1",
                tx_id="tx1",
                provider_event_id="evt1",
                finding_type="missing_in_ledger",
                severity="WARN",
                status="OPEN",
                message="Ledger missing for PSP event",
                raw={"example": True},
            )

            assert finding.id

            # List by provider
            items = await list_findings(session, provider="mockpsp")
            assert len(items) >= 1
            assert any(it.id == finding.id for it in items)

            # Resolve
            resolved = await resolve_finding(session, finding.id)
            assert resolved is not None
            assert resolved.status == "RESOLVED"

            # Filter by status
            open_items = await list_findings(session, status="OPEN")
            assert all(it.status == "OPEN" for it in open_items)

    asyncio.run(_run())
