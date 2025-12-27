# Architecture Snapshot (v1.0)

- **Backend:** FastAPI (Async) + SQLModel
- **DB:** PostgreSQL (Prod) / SQLite (Dev) - Managed via Alembic
- **Ledger:** Double-Entry Immutable Table (`ledgertransaction`)
- **Modules:** Payment, Risk, Poker, Growth (Offer/AB)
