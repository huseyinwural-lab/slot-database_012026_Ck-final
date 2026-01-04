# Payouts API (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Payments Engineering  

This document covers payout-related endpoints and the operational behavior around status polling.

---

## 1) Typical endpoints

Depending on deployment, payout endpoints may include:
- `GET /api/v1/payouts/status/{tx_id}` — payout status polling
- `POST /api/v1/payouts/*` — initiate or manage payouts

> Some environments keep payouts under `/api/v1/payments/*`. Treat this as a stable reference map, not a strict contract.

---

## 2) Status polling (ops notes)

Payout flows are often asynchronous:
- a payout is created
- provider processing happens in background
- the client polls status until final

Common CI/E2E flakiness mode:
- transient network errors during polling (`socket hang up`, timeouts)

Ops guidance:
- Prefer retry logic with bounded timeouts.
- Investigate backend logs with `request_id` correlation.

Legacy references:
- `/docs/E2E_SMOKE_MATRIX.md`
- `/docs/ops/webhook-failure-playbook.md`

---

## 3) Tenant scope

- All payout actions must be tenant-scoped.
- Owner may impersonate tenant using `X-Tenant-ID`.

See:
- `/docs/new/en/api/tenants.md`
- `/docs/new/en/admin/roles-permissions.md`
- `backend/app/core/tenant_context.py`
