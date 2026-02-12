# Risk Profile Schema

**Storage:** PostgreSQL
**Table:** `risk_profiles`

## 1. Schema Definition

```sql
CREATE TABLE risk_profiles (
    user_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    
    -- Scoring
    risk_score INT DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level VARCHAR(20) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH
    
    -- State
    flags JSONB DEFAULT '{}', -- Active flags e.g. {"churn_suspect": true}
    
    -- Velocity Counters (Simplified for Sprint 1 Persistence)
    -- In reality, detailed velocity might be in Redis, but snapshots here.
    last_withdrawal_at TIMESTAMP,
    deposit_count_24h INT DEFAULT 0,
    withdrawal_count_24h INT DEFAULT 0,
    
    -- Metadata
    last_updated_at TIMESTAMP DEFAULT NOW(),
    version INT DEFAULT 1
);
```

## 2. Persistence Strategy
- **Incremental Update:**
    -   Events trigger `RiskService`.
    -   `RiskService` calculates `delta`.
    -   `UPDATE risk_profiles SET risk_score = risk_score + delta ...`
-   **Consistency:**
    -   Transactional updates.
    -   Redis cache for fast read access during high-velocity gating.
