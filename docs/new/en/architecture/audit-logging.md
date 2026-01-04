# Logging & Audit (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Ops / Security  

This document ties together structured logging and audit requirements.

---

## 1) Structured logs

Canonical schema:
- `/docs/ops/log_schema.md`

Key fields:
- `request_id`
- `tenant_id`

---

## 2) Audit events (minimum set)

Audit should cover:
- tenant.created / tenant.disabled / tenant.deleted
- admin login failures
- policy changes
- break-glass actions

Implementation references:
- `backend/app/services/audit.py` (if present)
- calls in routes such as `backend/app/routes/tenant.py`

---

## 3) Break-glass logging

Any manual DB-created super admin or emergency changes must be:
- time-bounded
- reviewed
- logged (at least in ops ticket + audit record if possible)

---

## 4) Privacy / redaction

Never log:
- passwords
- bearer tokens
- secrets

See redaction rules:
- `/docs/ops/log_schema.md`
