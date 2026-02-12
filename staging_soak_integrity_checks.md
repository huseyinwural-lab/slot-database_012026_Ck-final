# Staging Soak Integrity Checks

**Frequency:** Every 12 Hours

## Check 1: Ledger Integrity
- Query: `SELECT count(*) FROM ledgertransaction WHERE status = 'failed'`
- Target: 0 (or explainable logic errors)

## Check 2: Idempotency
- Query: `SELECT provider_event_id, count(*) FROM game_events GROUP BY 1 HAVING count(*) > 1`
- Target: 0 rows

## Check 3: Orphan Wins
- Query: `SELECT count(*) FROM game_events WHERE type='WIN' AND round_id NOT IN (SELECT id FROM gameround)`
- Target: 0 rows
