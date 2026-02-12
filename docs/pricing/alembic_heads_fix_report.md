# Alembic Heads Fix Report

## Status: RESOLVED

### Diagnosis
- **Issue:** The `alembic_version` table contained two concurrent revisions (`phase4c_daily_aggregation` and `phase4b_currency_denorm`), causing a "multiple heads" or "overlap" conflict during upgrade.
- **Root Cause:** Likely a previous failed or manual migration that didn't clean up the version table, or a bad merge of branches.
- **Evidence:** `alembic heads` showed a single head (`phase4_real_final_v56`), but `alembic_version` table in SQLite had two rows.

### Resolution Steps
1.  **Analyzed History:** Confirmed `phase4c` revises `phase4b`.
2.  **Cleaned Version Table:** Manually deleted the redundant `phase4b_currency_denorm` row from `alembic_version` table.
3.  **Linearized Chain:** Created new migrations (`20260215_01` and `20260215_02`) that cleanly build upon `phase4_real_final_v56`.
4.  **Verified:** Ran `alembic upgrade head` successfully.

### Current State
- **Head:** `20260215_02_p1_discount_migration`
- **History:** Linear and consistent.
- **Database:** Fully up-to-date with P1.1 (Segmentation) and P1.2 (Discount) schemas.
