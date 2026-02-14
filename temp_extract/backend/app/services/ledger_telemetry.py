mismatch_counter = 0


def reset() -> None:
    global mismatch_counter
    mismatch_counter = 0


def record_balance_mismatch(
    *,
    tenant_id: str,
    player_id: str,
    currency: str,
    player_available: float,
    ledger_available: float,
) -> None:
    global mismatch_counter
    mismatch_counter += 1
    # TODO: add structured logging here if needed
