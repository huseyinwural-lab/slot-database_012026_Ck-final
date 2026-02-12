# Staging Soak Validation (Plan)

**Goal:** Long-running stability.

## 1. Schedule
- **Duration:** 5 Days.
- **Load:** Constant background chatter (10 TPS).
- **Events:** Daily Reconciliations.

## 2. Analysis
- **Memory:** Flat line (no leaks).
- **DB:** Predictable growth.
- **Logs:** Clean (no recurring errors).
