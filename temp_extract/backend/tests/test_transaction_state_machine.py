from __future__ import annotations


import pytest

from app.models.sql_models import Transaction
from app.services.transaction_state_machine import (
    STATE_CREATED,
    STATE_PENDING_PROVIDER,
    STATE_COMPLETED,
    STATE_REQUESTED,
    STATE_APPROVED,
    STATE_PAID,
    transition_transaction,
    ILLEGAL_STATE_ERROR_CODE,
)


@pytest.mark.parametrize(
    "tx_type, start_state, next_state",
    [
        ("deposit", STATE_CREATED, STATE_PENDING_PROVIDER),
        ("deposit", STATE_PENDING_PROVIDER, STATE_COMPLETED),
        ("withdrawal", STATE_REQUESTED, STATE_APPROVED),
        ("withdrawal", STATE_REQUESTED, "rejected"),
        ("withdrawal", STATE_APPROVED, STATE_PAID),
    ],
)
@pytest.mark.asyncio
async def test_allowed_transitions_succeed(tx_type: str, start_state: str, next_state: str):
    tx = Transaction(
        tenant_id="t1",
        player_id="p1",
        type=tx_type,
        amount=10.0,
        currency="USD",
        status="pending",
        state=start_state,
    )

    # Should not raise
    transition_transaction(tx, next_state)
    assert tx.state == next_state


@pytest.mark.parametrize(
    "tx_type, start_state, next_state",
    [
        ("deposit", STATE_CREATED, STATE_COMPLETED),  # skip pending_provider
        ("deposit", STATE_COMPLETED, STATE_PENDING_PROVIDER),
        ("withdrawal", STATE_APPROVED, "rejected"),
        ("withdrawal", STATE_PAID, STATE_APPROVED),
    ],
)
@pytest.mark.asyncio
async def test_illegal_transitions_raise_409(tx_type: str, start_state: str, next_state: str):
    from fastapi import HTTPException

    tx = Transaction(
        tenant_id="t1",
        player_id="p1",
        type=tx_type,
        amount=10.0,
        currency="USD",
        status="pending",
        state=start_state,
    )

    with pytest.raises(HTTPException) as exc_info:
        transition_transaction(tx, next_state)

    exc = exc_info.value
    assert exc.status_code == 409
    detail = exc.detail or {}
    assert detail.get("error_code") == ILLEGAL_STATE_ERROR_CODE
    assert detail.get("from_state") == start_state
    assert detail.get("to_state") == next_state
    assert detail.get("tx_type") == tx_type


@pytest.mark.asyncio
async def test_idempotent_same_state_is_noop():
    tx = Transaction(
        tenant_id="t1",
        player_id="p1",
        type="deposit",
        amount=10.0,
        currency="USD",
        status="pending",
        state=STATE_CREATED,
    )

    transition_transaction(tx, STATE_CREATED)
    assert tx.state == STATE_CREATED
