# Poker Provider Contract v1 (Cash)

**Version:** 1.0
**Date:** 2025-12-26

## 1. Overview
Standardized interface for Poker Game integration. Supports Cash Games via "Seamless Wallet".

## 2. Security
- **Authentication:** HMAC-SHA256 Signature + Timestamp.
- **Idempotency:** Required `transaction_id` (Provider TX ID) for all financial events.
- **Headers:** `X-Signature`, `X-Timestamp`.

## 3. Endpoints

### 3.1 Authentication
**POST** `/api/v1/integrations/poker/auth`
- **Input:** `token`
- **Output:** `player_id`, `currency`, `balance`

### 3.2 Transaction (Debit/Credit)
**POST** `/api/v1/integrations/poker/transaction`
- **Payload:**
  - `type`: `DEBIT` | `CREDIT` | `ROLLBACK`
  - `amount`: float
  - `round_id`: string (Hand ID)
  - `transaction_id`: string (Unique Provider TX ID)
- **Response:**
  - `status`: `OK`
  - `balance`: float
  - `ref`: string

### 3.3 Audit (Hand History)
**POST** `/api/v1/integrations/poker/hand-history`
- **Payload:**
  - `hand_id`: string
  - `table_id`: string
  - `game_type`: `CASH`
  - `pot_total`: float
  - `rake_collected`: float
  - `winners`: list
- **Response:** `OK`

## 4. Error Codes
- `INVALID_SIGNATURE` (401)
- `INSUFFICIENT_FUNDS` (402)
- `DUPLICATE_REQUEST` (409) - *Idempotent Replay handled as Success 200 with existing data*
- `INTERNAL_ERROR` (500)
