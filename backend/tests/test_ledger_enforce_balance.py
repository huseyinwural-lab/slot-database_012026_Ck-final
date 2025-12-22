import pytest
from sqlmodel import select

from config import settings
from app.repositories.ledger_repo import WalletBalance, LedgerTransaction, apply_balance_delta
from app.services import ledger_telemetry


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def extract_tx_id(json_body: dict) -> str:
    if "tx_id" in json_body:
        return str(json_body["tx_id"])
    if "id" in json_body:
        return str(json_body["id"])
    tx = json_body.get("transaction") or json_body.get("data", {}).get("transaction") or {}
    return str(tx.get("id") or tx.get("tx_id"))


@pytest.mark.asyncio
async def test_B01_enforce_on_idempotency_replay_same_tx_and_single_hold(
    async_session_factory,
    client,
    create_tenant,
    create_player_kyc_verified,
    login_player,
):
    settings.ledger_shadow_write = True
    settings.ledger_enforce_balance = True
    settings.ledger_balance_mismatch_log = True

    ledger_telemetry.reset()

    tenant = await create_tenant()
    player = await create_player_kyc_verified(
        tenant_id=tenant.id,
        balance_real_available=0.0,
    )

    token = await login_player(player)

    # fund via deposit so walletbalance has funds
    dep_headers = {"Idempotency-Key": "idem-dep-b01", **bearer(token)}
    dep = await client.post(
        "/api/v1/player/wallet/deposit",
        json={"amount": 100.0, "method": "test"},
        headers=dep_headers,
    )
    assert dep.status_code in (200, 201)

    idem = "idem-withdraw-enforce-1"
    w_headers = {"Idempotency-Key": idem, **bearer(token)}
    payload = {"amount": 10.0, "method": "test_bank", "address": "e2e"}

    r1 = await client.post("/api/v1/player/wallet/withdraw", json=payload, headers=w_headers)
    assert r1.status_code in (200, 201)
    tx1 = extract_tx_id(r1.json())

    r2 = await client.post("/api/v1/player/wallet/withdraw", json=payload, headers=w_headers)
    assert r2.status_code in (200, 201)
    tx2 = extract_tx_id(r2.json())

    assert tx2 == tx1

    async with async_session_factory() as session:
        wb = (
            await session.execute(
                select(WalletBalance).where(
                    WalletBalance.tenant_id == tenant.id,
                    WalletBalance.player_id == player.id,
                    WalletBalance.currency == "USD",
                )
            )
        ).scalars().first()
        assert wb is not None
        assert wb.balance_real_available == pytest.approx(90.0)
        assert wb.balance_real_pending == pytest.approx(10.0)

        evs = (
            await session.execute(
                select(LedgerTransaction).where(
                    LedgerTransaction.player_id == player.id,
                    LedgerTransaction.status == "withdraw_requested",
                    LedgerTransaction.idempotency_key == idem,
                )
            )
        ).scalars().all()
        assert len(evs) == 1


@pytest.mark.asyncio
async def test_B02_enforce_on_insufficient_funds_is_ledger_authority_fail_closed(
    async_session_factory,
    client,
    create_tenant,
    create_player_kyc_verified,
    login_player,
):
    settings.ledger_shadow_write = True
    settings.ledger_enforce_balance = True
    settings.ledger_balance_mismatch_log = True

    ledger_telemetry.reset()

    tenant = await create_tenant()
    player = await create_player_kyc_verified(
        tenant_id=tenant.id,
        balance_real_available=100.0,
    )

    token = await login_player(player)

    # No deposit => walletbalance is either missing or at 0
    r = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 10.0, "method": "test_bank", "address": "e2e"},
        headers={"Idempotency-Key": "idem-withdraw-b02", **bearer(token)},
    )
    assert r.status_code == 400
    body = r.json()
    err = body.get("error_code") or body.get("detail", {}).get("error_code")
    assert err == "INSUFFICIENT_FUNDS"

    # mismatch recorded (player 100 vs ledger 0)
    assert ledger_telemetry.mismatch_counter >= 1


@pytest.mark.asyncio
async def test_B03_enforce_off_legacy_behavior_and_mismatch_telemetry(
    async_session_factory,
    client,
    create_tenant,
    create_player_kyc_verified,
    login_player,
):
    settings.ledger_shadow_write = True
    settings.ledger_enforce_balance = False
    settings.ledger_balance_mismatch_log = True

    ledger_telemetry.reset()

    tenant = await create_tenant()
    player = await create_player_kyc_verified(
        tenant_id=tenant.id,
        balance_real_available=100.0,
    )

    token = await login_player(player)

    # Force ledger snapshot mismatch: create row with 0 available
    async with async_session_factory() as session:
        await apply_balance_delta(
            session,
            tenant_id=tenant.id,
            player_id=player.id,
            currency="USD",
            delta_available=0.0,
            delta_pending=0.0,
        )

    r = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 10.0, "method": "test_bank", "address": "e2e"},
        headers={"Idempotency-Key": "idem-withdraw-b03", **bearer(token)},
    )

    # legacy behavior: player had funds, withdraw should succeed
    assert r.status_code in (200, 201)

    assert ledger_telemetry.mismatch_counter >= 1


@pytest.mark.asyncio
async def test_B04_enforce_on_walletbalance_missing_is_fail_closed(
    async_session_factory,
    client,
    create_tenant,
    create_player_kyc_verified,
    login_player,
):
    settings.ledger_shadow_write = True
    settings.ledger_enforce_balance = True
    settings.ledger_balance_mismatch_log = True

    ledger_telemetry.reset()

    tenant = await create_tenant()
    player = await create_player_kyc_verified(
        tenant_id=tenant.id,
        balance_real_available=100.0,
    )

    token = await login_player(player)

    r = await client.post(
        "/api/v1/player/wallet/withdraw",
        json={"amount": 10.0, "method": "test_bank", "address": "e2e"},
        headers={"Idempotency-Key": "idem-withdraw-b04", **bearer(token)},
    )
    assert r.status_code == 400
    body = r.json()
    err = body.get("error_code") or body.get("detail", {}).get("error_code")
    assert err == "INSUFFICIENT_FUNDS"

    async with async_session_factory() as session:
        wb = (
            await session.execute(
                select(WalletBalance).where(
                    WalletBalance.tenant_id == tenant.id,
                    WalletBalance.player_id == player.id,
                    WalletBalance.currency == "USD",
                )
            )
        ).scalars().first()
        if wb is not None:
            assert wb.balance_real_available == pytest.approx(0.0)
