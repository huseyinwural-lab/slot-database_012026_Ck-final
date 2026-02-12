## Version
v1.0.0 — Production Ready Core

### Overview
This release marks the completion of the core Casino Platform infrastructure, ready for production deployment. It includes a fully functional player funnel, financial engine, game integration layer, and admin reporting system.

### Key Features
- **Wallet & Withdrawal Engine:**
  - Double-entry ledger system for financial integrity.
  - Withdrawal request flow with admin approval queue.
  - Balance locking logic (Available vs Held funds).
  - Idempotency guarantees for all financial transactions.

- **Game Engine (Provider Ready):**
  - Generic Provider Adapter architecture.
  - `GameRound` and `GameEvent` tracking.
  - Built-in Simulator provider for testing Bet/Win/Rollback cycles without external dependencies.
  - Multi-currency support (EUR/USD/TRY) with isolated wallets.

- **Security & Hardening:**
  - Abuse protection (Rate limiting, OTP lockout) using Redis.
  - Stripe Webhook signature verification and replay protection.
  - RBAC (Role-Based Access Control) for Admin/Ops actions.

- **Reporting & Analytics:**
  - Player Game History API.
  - Admin GGR (Gross Gaming Revenue) Reporting.
  - Hybrid Aggregation Layer: Combines real-time data with daily snapshots for scalable reporting.

### Tech Stack
- **Backend:** FastAPI, SQLAlchemy (Async), Alembic, Pydantic.
- **Frontend:** React, Vite, TailwindCSS, Shadcn UI.
- **Database:** PostgreSQL (Production), SQLite (Dev/Test).
- **Cache:** Redis (Production), InMemory Fallback (Dev).
- **Testing:** Playwright (E2E), Pytest (Unit/Integration).

### Deployment
Refer to `docker-compose.prod.yml` for production deployment configuration.
Ensure all secrets (`STRIPE_*`, `TWILIO_*`, `REDIS_URL`) are injected via environment variables.
