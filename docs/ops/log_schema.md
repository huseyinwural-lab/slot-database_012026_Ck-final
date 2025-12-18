# Log Schema Contract (P4.2)

This document defines the **canonical, stable JSON log fields** produced by the backend.

**Goal:** remove ambiguity for ops/alerting/incident response.

Scope:
- Applies to backend structured logs when `LOG_FORMAT=json`.
- Extra fields are allowed, but **MUST NOT** break or rename canonical fields.

---

## 1) Canonical fields (required)

| Field | Type | Required | Notes |
|---|---|---:|---|
| `timestamp` | string | yes | ISO-8601 UTC, e.g. `2025-12-18T20:07:55.180000+00:00` |
| `level` | string | yes | `INFO`/`WARNING`/`ERROR` |
| `message` | string | yes | Human-readable message |
| `service` | string | yes | e.g. `backend` |
| `env` | string | yes | `local`/`dev`/`staging`/`prod` |

Notes:
- `service` and `env` are included where available; they MUST be present on `event=service.boot`.

---

## 2) Event fields (optional but recommended)

| Field | Type | Required | Notes |
|---|---|---:|---|
| `event` | string | no | Stable event name for filtering/alerting. Example: `service.boot`, `request` |

### Standard event names
- `service.boot` — emitted on app startup (see `server.py` startup hook)
- `request` — emitted per HTTP request by RequestLoggingMiddleware

---

## 3) Request correlation & multi-tenancy

| Field | Type | Required | Notes |
|---|---|---:|---|
| `request_id` | string | no | Correlates FE errors and BE logs. Mirrors `X-Request-ID` |
| `tenant_id` | string | no | Tenant context. Mirrors `X-Tenant-ID` header when present |

---

## 4) HTTP request metrics (when `event=request`)

| Field | Type | Required | Notes |
|---|---|---:|---|
| `method` | string | no | `GET`, `POST`, ... |
| `path` | string | no | URL path only (no host/query), e.g. `/api/version` |
| `status_code` | number | no | HTTP status code |
| `duration_ms` | number | no | Request latency in ms |

---

## 5) Security / privacy (must-follow)

### 5.1 Redaction rules
Do **not** log raw credentials.

Any structured payload keys matching (case-insensitive) are redacted:
- `authorization`, `cookie`, `set-cookie`, `token`, `secret`, `api_key`

(Implementation reference: `backend/app/core/logging_config.py`.)

### 5.2 Identity fields
These may exist in log extras **if already safe/hashed**:
- `user_id` (string)
- `actor_user_id` (string)
- `ip` (string)

If you add them in the future, prefer:
- hashed identifiers (see security utils)
- avoid full IP storage unless needed for security investigations

---

## 6) Build metadata (required on `event=service.boot`)

When the service boots, log:
- `event=service.boot`
- `version`, `git_sha`, `build_time`

Used to answer: **"What release is running?"**

---

## 7) Alert mapping (P3.3 alignment)

This contract supports `docs/ops/alerts.md`:
- **5xx rate**: filter `event=request` and aggregate `status_code >= 500` per `path`
- **latency**: aggregate `duration_ms` (p95) per `path`
- **request correlation**: use `request_id`

Security/audit-based alerts should use **audit events** (DB-backed) where possible, and logs for triage.

---

## 8) Compatibility guarantee

- Canonical fields in sections (1), (3) and request metrics (4) MUST NOT be renamed.
- New fields may be added as extras.
- Removing fields requires a release note and ops sign-off.
