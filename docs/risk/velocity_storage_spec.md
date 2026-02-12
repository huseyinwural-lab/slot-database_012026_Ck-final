# Velocity Storage Specification

**Backend:** Redis (Persistent)
**Namespace:** `risk:velocity:`

## 1. Key Patterns

### A. Event Counters (e.g., Number of Withdrawals)
- **Key:** `risk:velocity:{metric}:{user_id}:{window_size}`
- **Type:** String (Integer with atomic INCR)
- **TTL:** `window_size` (seconds)

| Metric | Window | Redis Key Suffix | TTL |
|--------|--------|------------------|-----|
| Bet Count | 5m | `:bet_count:{uid}:300` | 300s |
| Withdrawal Count | 1h | `:wdraw_count:{uid}:3600` | 3600s |
| Deposit Count | 10m | `:dep_count:{uid}:600` | 600s |

### B. Amount Accumulators (e.g., Total Deposit Amount)
- **Key:** `risk:velocity:{metric}:{user_id}:{window_size}`
- **Type:** String (Float/Int with INCRBYFLOAT)
- **TTL:** `window_size` (seconds)

| Metric | Window | Redis Key Suffix | TTL |
|--------|--------|------------------|-----|
| Deposit Amount | 24h | `:dep_amt:{uid}:86400` | 86400s |
| Withdrawal Amount | 24h | `:wdraw_amt:{uid}:86400` | 86400s |

## 2. Implementation Logic
```python
key = f"risk:velocity:{metric}:{user_id}:{window}"
pipe = redis.pipeline()
pipe.incrby(key, amount) # or incr
pipe.expire(key, window, nx=True) # Set expire only if no expire exists
await pipe.execute()
```

## 3. Fallback
If Redis is unavailable:
- Log error `RISK_REDIS_DOWN`.
- Skip velocity check (Fail-Open) OR Flag as Medium Risk (Fail-Safe).
- **Decision:** Fail-Safe (Flag as Medium).
