# Observability (P2)

## 1) Request Correlation (X-Request-ID)
- Backend accepts incoming `X-Request-ID` **only** if it matches:
  - `^[A-Za-z0-9._-]{8,64}$`
- If missing/invalid, backend generates a UUID.
- Backend echoes the chosen value back in the **response header**:
  - `X-Request-ID: <value>`

### Why this matters
- Support/debug: a user can share a single ID to find all related logs.
- Safe-by-default: we ignore untrusted/oversized header values.

## 2) JSON Logs (prod/staging default)
- `ENV=prod|staging` ⇒ JSON logs are the default (`LOG_FORMAT=auto`).
- `ENV=dev|local` ⇒ human-readable logs are the default.
- Override is always possible:
  - `LOG_FORMAT=json` or `LOG_FORMAT=plain`

### Recommended log fields (Kibana/Grafana)
Stable fields to index:
- `timestamp` (ISO, UTC)
- `level`
- `message`
- `event` (when present)
- `request_id`
- `tenant_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `client_ip` (when present, e.g. rate-limit events)

Example Kibana query ideas:
- Find a single request:
  - `request_id:"<id>"`
- Rate limiting events:
  - `event:"auth.login_rate_limited"`

## 3) Sensitive Data Masking
The JSON logger redacts keys (case-insensitive) anywhere inside structured payloads:
- `authorization`, `cookie`, `set-cookie`, `password`, `token`, `secret`, `api_key`

> Note: This applies to structured `extra={...}` payloads. Avoid logging raw headers / tokens into the free-text message.

## 4) Health vs Readiness
- **Liveness**: `GET /api/health`
  - Process is up
- **Readiness**: `GET /api/ready` (alias of `/api/readiness`)
  - DB connectivity check (`SELECT 1`)
  - Lightweight migration state check via `alembic_version`

In Docker Compose, the backend container healthcheck targets `/api/ready`.
