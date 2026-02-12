# Admin Risk Dashboard Schema

**Module:** Operational Control
**Access:** Admin/RiskRole Only

## 1. Data Model Extensions

### A. Risk History Table
To audit changes and visualize timeline.
```sql
CREATE TABLE risk_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    old_score INT,
    new_score INT,
    change_reason VARCHAR, -- "Rule: Velocity", "Manual: Admin"
    changed_by UUID, -- Admin ID or System
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 2. API Endpoints

### A. Get User Risk Profile
`GET /api/v1/admin/risk/{user_id}`
-   Returns: Current Score, Level, Active Flags, Velocity Snapshots.

### B. Get User Risk History
`GET /api/v1/admin/risk/{user_id}/history`
-   Returns: List of score changes.

### C. Manual Override
`POST /api/v1/admin/risk/{user_id}/override`
-   Payload: `{ "score": 50, "reason": "Suspected multi-accounting" }`
-   Action: Updates `RiskProfile`, Logs to `RiskHistory`.

## 3. Dashboard UI Views (Mock)
-   **Search:** By UserID / Email.
-   **Profile Card:** Big colored badge (Green/Yellow/Red) for Level.
-   **Timeline:** Vertical list of events (Deposits, Withdrawals, Score Changes).
-   **Actions:** "Reset Score", "Freeze Account" buttons.
