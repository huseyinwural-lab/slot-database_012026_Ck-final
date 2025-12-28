# P1-B-S: Minimal Money-Loop Smoke (External Env) — Go/No-Go Gate

## Scope
This smoke validates **wallet/ledger invariants** on external Postgres + external Redis, using the fastest PSP-free path:
- Admin manual credit/debit / ledger adjust (no PSP/webhooks)
- Idempotency enforced via `Idempotency-Key` header
- Evidence is URL-less (masked)

This is a **Go/No-Go** gate. If it fails, no release.

---

## Preconditions
- P1-B readiness gate passes:
  - `GET /api/ready` = 200
  - `dependencies.database=connected`
  - `dependencies.redis=connected`
  - `dependencies.migrations=head` (or equivalent)
- Environment:
  - `ENV=staging` (or prod-like)
  - `CI_STRICT=1` recommended for strict behavior
- Masking rules: secrets and credentials must be replaced with `***`.

---

## Canonical Endpoints (this repo)
These are the canonical endpoints to use for this smoke in this codebase:

- Ready gate:
  - `GET /api/ready`
  - `GET /api/version`

- Player create (admin):
  - `POST /api/v1/players`

- Wallet + ledger snapshots (admin):
  - `GET /api/v1/admin/players/{player_id}/wallet`
  - `GET /api/v1/admin/players/{player_id}/ledger/balance`

- Manual adjust (admin, PSP-free):
  - `POST /api/v1/admin/ledger/adjust`
    - Body: `{ "player_id": "...", "delta": 100, "reason": "...", "currency": "USD" }`
    - Header: `Idempotency-Key: ...`

---

## Entities & Notation
- Player: `player_id`
- Wallet balance: `wallet_balance`
- Ledger balance: `ledger_balance`
- Currency: use the default system currency (`USD`) unless your deployment config differs.

**Invariant:** After each operation, `wallet_balance.total_real == ledger_balance.total_real` for the currency scope.

---

## Evidence Output Template (Audit Trail)
Use the same structure as `docs/P1B_SELF_SERVE.md` evidence template:
- Timestamp (UTC), environment, `/api/version`, runner (masked)
- For each command: command + HTTP status + response + exit code

---

## Step 0 — Ready Gate
```bash
curl -sS -i http://localhost:8001/api/ready
echo "EXIT_CODE=$?"
curl -sS -i http://localhost:8001/api/version
echo "EXIT_CODE=$?"
```

GO: `/api/ready` = 200

NO-GO: non-200

---

## Step 1 — Create Player
Use the canonical endpoint from this repo.

```bash
curl -sS -i -X POST http://localhost:8001/api/v1/players \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{ "email":"p1b_smoke_***@example.com", "username":"p1b_smoke_user", "password":"***" }'
echo "EXIT_CODE=$?"
```

Record `player_id` from the response.

GO: 201/200 with a valid `player_id`

NO-GO: non-2xx

---

## Step 2 — Snapshot Before (Wallet + Ledger)
```bash
# Wallet snapshot
curl -sS -i http://localhost:8001/api/v1/admin/players/${player_id}/wallet \
  -H "Authorization: Bearer ***"
echo "EXIT_CODE=$?"

# Ledger snapshot
curl -sS -i http://localhost:8001/api/v1/admin/players/${player_id}/ledger/balance \
  -H "Authorization: Bearer ***"
echo "EXIT_CODE=$?"
```

GO: responses are 200 and consistent

NO-GO: non-200 or mismatch already exists

---

## Step 3 — Manual Credit (Idempotent)
Choose an amount, e.g. +100.

```bash
curl -sS -i -X POST http://localhost:8001/api/v1/admin/ledger/adjust \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: p1b-credit-001" \
  -d '{ "player_id":"'"${player_id}"'", "delta": 100, "reason":"P1-B-S smoke credit", "currency":"USD" }'
echo "EXIT_CODE=$?"
```

Re-run the exact same request (same `Idempotency-Key`).

GO:
- First call: 2xx
- Second call: 2xx AND no additional delta applied (`idempotent_replay=true` or equivalent)
- Post-state: wallet and ledger totals increased by **+100 exactly once**

NO-GO: double credit or wallet/ledger mismatch

---

## Step 4 — Manual Debit (Idempotent)
Choose an amount, e.g. -40.

```bash
curl -sS -i -X POST http://localhost:8001/api/v1/admin/ledger/adjust \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: p1b-debit-001" \
  -d '{ "player_id":"'"${player_id}"'", "delta": -40, "reason":"P1-B-S smoke debit", "currency":"USD" }'
echo "EXIT_CODE=$?"
```

Re-run the same request with the same `Idempotency-Key`.

GO:
- Applied exactly once
- Post-state: balances decreased by **40 exactly once**
- `wallet_balance.total_real == ledger_balance.total_real`

NO-GO: double debit or mismatch

---

## Step 5 — Optional (Strong) DB Evidence
If you have a secure admin-only endpoint to list ledger events, record:
- exactly one event for `p1b-credit-001`
- exactly one event for `p1b-debit-001`

(Out of scope for this doc if endpoint is not available.)

---

## Go / No-Go Summary
GO if ALL true:
- `/api/ready` = 200
- Manual credit applied exactly once under idempotency replay
- Manual debit applied exactly once under idempotency replay
- After each step, `wallet_balance.total_real == ledger_balance.total_real`

NO-GO if ANY true:
- ready non-200
- duplicate application under same idempotency key
- wallet/ledger mismatch at any point
- non-deterministic behavior across replays

---

## Follow-up (out of scope for this doc)
- PSP sandbox flow (Stripe/Adyen) including webhook + idempotency (P1-B-S2)
- Withdraw hold/approve/paid lifecycle smoke (if not covered by adjust endpoints)

---

## APPENDIX: One-shot evidence capture (single paste)

### Goal
Run G0→G4 in one go, keep output order deterministic, and share as a single paste.

### Usage
1) Set `BASE_URL` and `ADMIN_JWT` in your external environment shell.
2) Run the script below.
3) Copy the entire output and paste it back to this channel.
4) Before sharing, mask only secrets/tokens/credentials as per rules.

### One-shot command (bash)
```bash
set -euo pipefail

BASE_URL="${BASE_URL:?set BASE_URL}"
ADMIN_JWT="${ADMIN_JWT:?set ADMIN_JWT}"

# helper: request wrapper
req() { bash -c "$1"; echo; }

echo -e "\n===== G0: /api/ready =====\n"
req "curl -sS -i \"$BASE_URL/api/ready\""

echo -e "\n===== G0: /api/version =====\n"
req "curl -sS -i \"$BASE_URL/api/version\""

echo -e "\n===== G1: POST /api/v1/players =====\n"
# IMPORTANT: prefer canonical payload from this doc.
# Below is a common-safe payload; adjust if validation fails (e.g., username required).
PLAYER_CREATE_RESP="$(curl -sS -i -X POST \"$BASE_URL/api/v1/players\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -d '{"email":"p1b_smoke_'$(date +%s)'@example.com","username":"p1b_smoke_'$(date +%s)'","password":"TempPass!123"}')"
echo "$PLAYER_CREATE_RESP"
echo

# Extract player_id if present (best-effort; works if body contains "id" or "player_id")
PLAYER_ID="$(echo "$PLAYER_CREATE_RESP" | tail -n 1 | sed -n 's/.*"player_id"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p')"
if [ -z "${PLAYER_ID:-}" ]; then
  PLAYER_ID="$(echo "$PLAYER_CREATE_RESP" | tail -n 1 | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p')"
fi

if [ -z "${PLAYER_ID:-}" ]; then
  echo -e "\n===== STOP: player_id not found (G1 likely FAIL). Paste output as-is for NO-GO evaluation. =====\n"
  exit 0
fi

echo -e "\n===== G2: Wallet before =====\n"
req "curl -sS -i \"$BASE_URL/api/v1/admin/players/$PLAYER_ID/wallet\" -H \"Authorization: Bearer $ADMIN_JWT\""

echo -e "\n===== G2: Ledger before =====\n"
req "curl -sS -i \"$BASE_URL/api/v1/admin/players/$PLAYER_ID/ledger/balance\" -H \"Authorization: Bearer $ADMIN_JWT\""

echo -e "\n===== G3: Credit + replay (Idempotency-Key: p1b-credit-001) =====\n"
req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-credit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":100,"reason":"P1-B-S smoke credit","currency":"USD"}'"

req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-credit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":100,"reason":"P1-B-S smoke credit","currency":"USD"}'"

echo -e "\n===== G4: Debit + replay (Idempotency-Key: p1b-debit-001) =====\n"
req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-debit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":-40,"reason":"P1-B-S smoke debit","currency":"USD"}'"

req "curl -sS -i -X POST \"$BASE_URL/api/v1/admin/ledger/adjust\" \
  -H \"Authorization: Bearer $ADMIN_JWT\" \
  -H \"Content-Type: application/json\" \
  -H \"Idempotency-Key: p1b-debit-001\" \
  -d '{"player_id":"$PLAYER_ID","delta":-40,"reason":"P1-B-S smoke debit","currency":"USD"}'"

echo -e "\n===== DONE: Paste this entire output (mask tokens only) =====\n"
```

### Masking reminder
- Mask only: `Authorization: Bearer <token>` → `Authorization: Bearer ***`
- Do NOT mask: `player_id`, HTTP status codes, `idempotent_replay`
