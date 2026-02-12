# P1 Segmentation Prod Validation (Dry Run Plan)

**Objective:** Verify migration safety on PostgreSQL before live deploy.

## 1. Enumerated Type Safety
- **Risk:** Creating ENUM inside a transaction.
- **Check:** Ensure `create_type=False` is handled if type already exists.
- **Script:** `SELECT typname FROM pg_type WHERE typname = 'segment_type';`

## 2. Backfill Performance
- **Query:** `UPDATE users SET segment_type = 'INDIVIDUAL' WHERE segment_type IS NULL`
- **Lock Check:** Ensure batch update or lock timeout is configured if user table > 100k rows.

## 3. Rollback Test
1. Apply migration.
2. Verify `segment_type` column exists.
3. Rollback migration.
4. Verify column is gone AND Enum type is dropped (or preserved safely).

## 4. Constraint Validation
- Insert `NULL` -> Must Fail.
- Insert `INVALID_ENUM` -> Must Fail.
- Insert `INDIVIDUAL` -> Success.
