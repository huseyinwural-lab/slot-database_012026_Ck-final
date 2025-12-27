# Log Schema v1

## Overview
This schema defines the structured JSON log format used across all backend services (Payments, Risk, Poker, Bonus).
The goal is to ensure logs are machine-parsable for observability tools (Datadog, CloudWatch, ELK).

## Standard Fields (Mandatory)

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO8601 String | UTC timestamp of the event. |
| `level` | String | Log level (INFO, WARN, ERROR, CRITICAL). |
| `message` | String | Human-readable message. |
| `request_id` | UUID | Correlation ID for HTTP requests. |
| `tenant_id` | String | Tenant context (if applicable). |

## Context Fields (Domain Specific)

These fields are injected via `extra={...}` dictionary in python logging calls.

### Payments
| Field | Type | Description |
|---|---|---|
| `payment_intent_id` | UUID | The main payment session ID. |
| `provider` | String | Payment provider (stripe, adyen). |
| `amount` | Float | Transaction amount. |
| `currency` | String | Currency code (USD). |

### Poker / Game
| Field | Type | Description |
|---|---|---|
| `game_session_id` | UUID | Session ID. |
| `round_id` | UUID | Game round ID. |
| `table_id` | String | Poker table ID. |

### Risk / Compliance
| Field | Type | Description |
|---|---|---|
| `player_id` | UUID | Subject player ID. |
| `risk_score` | String | Risk assessment result. |
| `signal_type` | String | Risk signal (e.g. collusion). |

## Redaction Policy
The following keys are automatically redacted (replaced with `[REDACTED]`):
- `password`, `token`, `secret`, `authorization`, `cookie`, `api_key`

## Example

```json
{
  "timestamp": "2025-12-27T10:00:00.123Z",
  "level": "INFO",
  "message": "Payment authorized successfully",
  "request_id": "a1b2c3d4...",
  "tenant_id": "default_casino",
  "payment_intent_id": "pay_12345",
  "provider": "stripe",
  "amount": 100.0,
  "currency": "USD"
}
```
