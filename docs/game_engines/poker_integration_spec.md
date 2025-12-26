# Poker Integration Specification

**Version:** 1.0
**Date:** 2025-12-26

## 1. Overview
The integration follows a "Seamless Wallet" model where the Provider acts as the Game Engine, and our platform acts as the Wallet/Ledger.

## 2. API Endpoints

### 2.1 Launch Authentication
**POST** `/api/v1/integrations/poker/auth`
- **Input:** `token`
- **Output:** `player_id`, `currency`, `balance`

### 2.2 Transaction (Debit/Credit)
**POST** `/api/v1/integrations/poker/transaction`
- **Payload:**
  - `type`: `DEBIT` (Buy-in/Bet) or `CREDIT` (Win/Cashout)
  - `amount`: float
  - `round_id`: string (Hand ID)
  - `transaction_id`: string (Unique Provider TX ID)
- **Response:**
  - `status`: `OK`
  - `balance`: float (New Balance)
  - `ref`: string (Platform TX ID)

### 2.3 Hand History (Audit)
**POST** `/api/v1/integrations/poker/hand-history`
- **Payload:**
  - `hand_id`: string
  - `pot_total`: float
  - `rake_collected`: float
  - `winners`: list
- **Response:** `OK`

## 3. Rake & Economy
- **Rake Calculation:** Verified internally. Discrepancies > 1% trigger alerts.
- **Rakeback:** Calculated daily based on `rake_collected`.

## 4. Security
- **Idempotency:** Required on `transaction_id`.
- **Signature:** HMAC-SHA256 required on headers.
