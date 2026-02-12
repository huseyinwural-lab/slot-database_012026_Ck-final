# Bet Throttling Model v1

**Type:** Hard Cap + Risk-Adjusted Dynamic Limit
**Implementation:** Redis Token Bucket

## 1. Throttling Tiers

| Risk Level | Max Bets / Minute | Burst Allowance | Action |
|------------|-------------------|-----------------|--------|
| **LOW** | 60 (1/sec avg) | 10 | Throttle (HTTP 429) |
| **MEDIUM** | 30 (0.5/sec avg) | 5 | Throttle (HTTP 429) |
| **HIGH** | 10 (0.16/sec avg) | 0 | Throttle (HTTP 429) + Alert |

## 2. Technical Design
- **Key:** `risk:throttle:bet:{user_id}`
- **Algorithm:**
    -   `INCR` key.
    -   `EXPIRE` 60s (if new).
    -   Check value > Limit.
-   **Latency:** < 5ms added to Game Launch/Spin.

## 3. Integration Point
- **Option A:** `GameEngine.process_spin()` (Backend).
- **Option B:** API Middleware (Edge).
- **Decision:** Backend `GameEngine`. Allows provider-agnostic throttling even for server-to-server callbacks if we map session to user.

## 4. User Experience
-   **Client:** Receives error `429 Too Many Requests`.
-   **UI:** Shows "Please slow down" toast notification.
