# UI Publish Readiness Report (Plan)

**Goal:** Zero broken windows.

## 1. Route Audit
- [ ] `/lobby`: Games load.
- [ ] `/wallet`: Balance updates.
- [ ] `/history`: Transactions appear.
- [ ] `/admin`: Dashboard functional.

## 2. Feature Flags
- `PRAGMATIC_ENABLED`: True/False.
- `RISK_DASHBOARD_ENABLED`: True/False.

## 3. Console Hygiene
- No `console.error` on critical paths.
- No debug logs in Production build.
