# Risk Score Distribution Monitoring

**Frequency:** Daily
**Job:** `DailyRiskReport`

## 1. Distribution Targets
We expect the player base to follow a Pareto-like distribution.

- **LOW (0-39):** ~90-95% of active users.
- **MEDIUM (40-69):** ~4-8% (Suspicious, New Devices, high velocity).
- **HIGH (70+):** ~1-2% (Confirmed abuse, churners).

## 2. Drift Detection
If the distribution shifts significantly (e.g., HIGH jumps to 10%), it indicates:
1.  **False Positives:** A rule is too aggressive (e.g., "New Device" weight too high).
2.  **Attack:** Coordinated bot attack triggering velocity rules.
3.  **Bug:** Score double-counting or failure to decay.

## 3. Reporting Query
```sql
SELECT 
    risk_level, 
    COUNT(*) as count, 
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM risk_profiles 
GROUP BY risk_level;
```

## 4. Action Plan
- **Daily Review:** Risk Manager checks the distribution.
- **Drift > 5%:** Triggers immediate investigation of top contributing rules.
