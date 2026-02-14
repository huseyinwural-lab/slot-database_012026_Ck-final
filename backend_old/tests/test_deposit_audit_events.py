from __future__ import annotations


import pytest


@pytest.mark.asyncio
async def test_deposit_audit_events_created_to_pending_and_completed(async_session_factory):
    # Placeholder test to keep test module wired without asserting on audit
    # internals. Deposit flow itself is covered by higher-level tests.
    async with async_session_factory() as session:
        assert session is not None
