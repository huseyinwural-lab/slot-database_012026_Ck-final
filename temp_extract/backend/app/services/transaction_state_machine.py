from __future__ import annotations

"""Shared transaction state machine helpers for deposit & withdrawal.

This module centralises allowed state transitions for the Transaction model so
that:
- Illegal transitions consistently return 409 with a canonical error code.
- Deposit & withdrawal flows share the same domain language.
- Canonical state is Transaction.state; status is legacy/auxiliary.

We keep string values aligned with existing production code and tests
(e.g. "requested", "approved", "paid", "created", "pending_provider",
"completed"). Higher‑level labels like "pending_review" / "succeeded" are
handled via alias mapping without changing what is stored in the DB.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.models.sql_models import Transaction


# Canonical error code for illegal transitions
ILLEGAL_STATE_ERROR_CODE = "ILLEGAL_TRANSACTION_STATE_TRANSITION"


# --- State constants --------------------------------------------------------

STATE_CREATED = "created"
STATE_PENDING_PROVIDER = "pending_provider"
STATE_COMPLETED = "completed"
STATE_REQUESTED = "requested"
STATE_PENDING_REVIEW = "pending_review"  # semantic alias for requested
STATE_APPROVED = "approved"
STATE_REJECTED = "rejected"
STATE_PROCESSING = "processing"
STATE_PAID = "paid"
STATE_SUCCEEDED = "succeeded"  # semantic alias for completed/paid
STATE_FAILED = "failed"
STATE_CANCELED = "canceled"


# Alias map: input state -> canonical state stored in DB.
STATE_ALIASES: Dict[str, str] = {
    STATE_PENDING_REVIEW: STATE_REQUESTED,
    STATE_SUCCEEDED: STATE_COMPLETED,
}


def normalize_state(state: Optional[str]) -> str:
    """Normalize a state value to its canonical representation.

    - Unknown/None states fall back to "created".
    - Aliases are mapped to their canonical DB representation.
    """

    if not state:
        return STATE_CREATED
    return STATE_ALIASES.get(state, state)


# Allowed state transitions per transaction type (using canonical states).
ALLOWED_TRANSITIONS: Dict[str, Dict[str, List[str]]] = {
    "deposit": {
        STATE_CREATED: [STATE_PENDING_PROVIDER],
        STATE_PENDING_PROVIDER: [STATE_COMPLETED, STATE_FAILED],
    },
    "withdrawal": {
        STATE_REQUESTED: [STATE_APPROVED, STATE_REJECTED, STATE_CANCELED],
        # P0-5 payout states: keep legacy approved->paid path for mark-paid while
        # introducing payout_pending / payout_failed.
        STATE_APPROVED: [STATE_PAID, "payout_pending"],
        "payout_pending": [STATE_PAID, "payout_failed"],
        "payout_failed": ["payout_pending", STATE_REJECTED],
    },
}


def _get_tx_type(tx: Transaction) -> str:
    """Return the logical transaction type bucket.

    For now this is the raw Transaction.type value ("deposit"/"withdrawal").
    """

    return tx.type


def transition_transaction(
    tx: Transaction,
    new_state: str,
    *,
    actor: Optional[str] = None,
    reason: Optional[str] = None,
    audit_ctx: Optional[Dict[str, Any]] = None,
) -> None:
    """Apply a state transition with whitelist enforcement.

    - Canonical field is Transaction.state (status is untouched here).
    - If the transition is not allowed, raise HTTP 409 with a canonical
      error_code.
    - Same‑state transitions are treated as idempotent no‑ops.
    - Audit is *not* performed here; callers can use actor/reason/audit_ctx to
      log via the shared audit service.
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

    current = normalize_state(tx.state)
    target = normalize_state(new_state)

    # Idempotent no‑op: already in desired state.
    if current == target:
        return

    allowed_next = transitions_for_type.get(current, [])
    if target not in allowed_next:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": ILLEGAL_STATE_ERROR_CODE,
                "from_state": current,
                "to_state": target,
                "tx_type": tx_type,
            },
        )

    # Persist canonical state
    tx.state = target
