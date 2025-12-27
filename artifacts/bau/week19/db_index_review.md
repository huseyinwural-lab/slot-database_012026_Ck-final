# DB Index Review

## Overview
Analysis of critical query paths and supporting indexes.

## Critical Tables & Indexes

### 1. Transactions & Payments
- **Table:** `transaction`
  - `ix_transaction_player_id`: Essential for wallet history.
  - `ix_transaction_tenant_id`: Multi-tenancy isolation.
  - `ux_tx_provider_event`: Idempotency guard.
- **Table:** `payoutattempt`
  - `ix_payoutattempt_status`: Polling for pending payouts.
  - `ix_payoutattempt_idempotency_key`: Safety.

### 2. Risk & Compliance
- **Table:** `risksignal`
  - `ix_risksignal_player_id`: Risk profile lookup.
  - `created_at` (Missing Index?): Needed for "Last Hour" window queries in AlertEngine.
  - *Recommendation:* Add index on `risksignal(created_at)`.

### 3. Growth & Offers
- **Table:** `offerdecisionrecord`
  - `ix_offerdecisionrecord_player_id`: Player history.
  - `ix_offerdecisionrecord_tenant_id`: Isolation.
  - `trigger_event`: Frequent filtering. Consider index if high cardinality.

### 4. Poker
- **Table:** `pokertournament`
  - `ix_pokertournament_status`: Lobby filtering.
- **Table:** `tournamentregistration`
  - `ix_tournamentregistration_player_id`: Re-entry check.
  - `ix_tournamentregistration_tournament_id`: Entrant list.

## Missing Indexes Identified
1. `risksignal.created_at`: Critical for windowed aggregations (Alerts).
2. `offerdecisionrecord.trigger_event`: Useful for analytics.

*Action:* Not creating migration now as volume is low, but added to backlog T19-Backlog.
