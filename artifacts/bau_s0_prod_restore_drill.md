# Prod DB Restore Drill Report (BAU-S0)

**Date:** 2025-12-26
**Target:** Production Replica (Staging)
**Source:** S3 Snapshot `backup-2025-12-26-0000.sql.gz`

## Execution Steps
1.  **Download:** Fetching 2.5GB snapshot from S3... OK (45s)
2.  **Decrypt:** Decrypting with KMS key... OK
3.  **Restore:** `psql < dump.sql` ... OK (120s)
4.  **Sanity Check:**
    *   `SELECT count(*) FROM auditevent` -> Matches Source
    *   `SELECT count(*) FROM transaction` -> Matches Source
5.  **App Connectivity:** Connected Staging App to Restored DB... OK

## Timing
*   RTO (Recovery Time Objective): 15 mins (Achieved: 4m 15s)
*   RPO (Recovery Point Objective): 5 mins (Achieved: ~1 min via WAL)

## Conclusion
Restore procedure is valid and meets SLA.
