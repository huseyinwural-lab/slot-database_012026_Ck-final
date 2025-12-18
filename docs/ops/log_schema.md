# Log Schema (P3-OBS-002)

This document defines the **common JSON log fields** produced by the backend.

## Canonical fields
- `timestamp` (ISO-8601, UTC)
- `level`
- `message`
- `event` (stable event name when applicable)
- `service`
- `env`

## Request correlation
- `request_id`
- `tenant_id`

## HTTP request metrics (when logged)
- `method`
- `path`
- `status_code`
- `duration_ms`

## Security / privacy
- Do **not** log raw credentials.
- Any structured payload keys matching: `authorization`, `cookie`, `set-cookie`, `token`, `secret`, `api_key` are redacted.

## Build metadata
On boot, backend logs:
- `event=service.boot`
- `version`, `git_sha`, `build_time`

Use these fields to identify what release is currently running.
