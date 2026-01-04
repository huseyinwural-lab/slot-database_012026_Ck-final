# Performance & Guardrails (EN)

**Last reviewed:** 2026-01-04  
**Owner:** Platform Engineering  

This document defines practical guardrails so the system behaves predictably under load.

---

## 1) Rate limiting

The backend includes a simple in-memory rate limiter for critical endpoints.

Implementation:
- `backend/app/middleware/rate_limit.py`

Notes:
- dev/local/test/ci environments relax limits
- prod/staging are stricter (e.g., login)

Caveat:
- in-memory rate limiting is node-local; for multi-node you need a shared limiter (Redis / gateway).

---

## 2) High-cost operations

Examples of high-cost actions:
- tenant purge / destructive cleanup
- large backfills
- mass user operations

Guidance:
- require platform owner authorization
- run as background job
- track progress and log audit events

---

## 3) Background jobs

Document for your deployment:
- scheduler/worker used
- queue backend
- retry policy
- dead-letter strategy

---

## 4) Big tenants

Operational notes:
- expect longer payout state transitions
- prefer bounded polling and robust retry handling
- plan maintenance windows for heavy migrations
