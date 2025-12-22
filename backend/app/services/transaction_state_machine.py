from __future__ import annotations

"""Shared transaction state machine helpers for deposit & withdrawal.

This module centralises allowed state transitions for the Transaction model so
that:
- Illegal transitions consistently return 409 with a canonical error code.
- Deposit & withdrawal flows share the same domain language.

NOTE:
- We intentionally keep the actual string values aligned with existing
  production code and tests (e.g. "requested", "approved", "paid",
  "created", "pending_provider", "completed"). Higher‑level labels like
  "pending_review" / "succeeded" can be layered on top in future phases
  without breaking DB state.
"""

from typing import Dict, List

from fastapi import HTTPException

from app.models.sql_models import Transaction


# Canonical error code for illegal transitions
ILLEGAL_STATE_ERROR_CODE = "ILLEGAL_TRANSACTION_STATE_TRANSITION"


# Allowed state transitions per transaction type.
#
# We keep this minimal and focused on currently implemented flows:
# - Deposit: created -> pending_provider -> completed
# - Withdrawal: requested -> approved/rejected -> paid
#
# Additional states like "processing", "failed", "canceled" can be wired
# in later without changing callers.
ALLOWED_TRANSITIONS: Dict[str, Dict[str, List[str]]] = {
    "deposit": {
        "created": ["pending_provider"],
        "pending_provider": ["completed"],
    },
    "withdrawal": {
        "requested": ["approved", "rejected"],
        "approved": ["paid"],
    },
}


def _get_tx_type(tx: Transaction) -> str:
    """Return the logical transaction type bucket.

    For now this is the raw Transaction.type value ("deposit"/"withdrawal").
    """

    return tx.type


def transition_transaction(tx: Transaction, new_state: str) -> None:
    """Apply a state transition with whitelist enforcement.

    - If the transition is not allowed, raise HTTP 409 with a canonical
      error_code.
    - The caller is responsible for persisting the transaction and logging
      any audit events. This keeps the helper side‑effect free beyond the
      in‑memory state change.
    """

    tx_type = _get_tx_type(tx)
    transitions_for_type = ALLOWED_TRANSITIONS.get(tx_type)
    if not transitions_for_type:
        # For unknown types we fail hard – this should not happen for
        # deposit/withdrawal.
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ILLEGAL_STATE_ERROR_CODE,
                "message": f"Unsupported transaction type: {tx_type}",
            },
        )

    current = tx.state or "created"

    # Idempotent no‑op: already in desired state.
    if current == new_state:
        return

    allowed_next = transitions_for_type.get(current, [])
    if new_state not in allowed_next:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": ILLEGAL_STATE_ERROR_CODE,
                "from_state": current,
                "to_state": new_state,
                "tx_type": tx_type,
            },
        )

    tx.state = new_state
