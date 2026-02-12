# P1 Segmentation Migration Plan

**Critical Path:** Zero downtime deployment.

## Phase 1: Schema Change
1. Add `segment_type` column to `users` table.
2. Allow NULL initially (to prevent lock).
3. Set Default = 'INDIVIDUAL'.

## Phase 2: Data Backfill
1. Run script to update all existing `NULL` records to `INDIVIDUAL`.
   ```sql
   UPDATE users SET segment_type = 'INDIVIDUAL' WHERE segment_type IS NULL;
   ```
2. Verify no NULLs remain.

## Phase 3: Constraint Enforcement
1. Alter column to `NOT NULL`.
2. Commit.

## Phase 4: Code Deployment
1. Deploy code that expects `segment_type` (P1.1 release).
2. Prior to this, code must handle legacy/missing segment gracefully (fail closed or default to individual).

## Verification
- Run `SELECT count(*) FROM users WHERE segment_type IS NULL` -> Must be 0.
