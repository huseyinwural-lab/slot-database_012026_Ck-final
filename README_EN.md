# Casino Platform - User Manual

This project is a highly regulated, auditable, and scalable **Casino and Betting Platform**.
It includes a financial ledger, risk management, multiplayer poker engine, bonus engine, and a modern administration panel.

---

## 🏗️ Architectural Overview

*   **Backend:** Python (FastAPI), AsyncIO, SQLModel (ORM).
*   **Database:** PostgreSQL (Prod), SQLite (Dev). All schema changes are managed via **Alembic**.
*   **Frontend:** React, Tailwind CSS, Shadcn UI.
*   **Operations:** Services managed by Supervisor, Docker-compatible structure.

### Key Modules
1.  **Core Finance (Ledger):** Double-entry accounting system. Every transaction (Deposit, Bet, Win, Withdraw) is stored in the `ledgertransaction` table with a hash chain.
2.  **Poker Engine:** Multi-Table Tournament (MTT) and Cash Game support.
3.  **Risk & Compliance:** KYC (Know Your Customer), RG (Responsible Gaming), and Collusion detection.
4.  **Growth:** Affiliate system, A/B testing, and Smart Offer engine.

---

## 🚀 Installation and Execution

### Prerequisites
*   Python 3.11+
*   Node.js 18+ (Yarn)
*   PostgreSQL (Optional, SQLite is default for local dev)

### Setup Steps

> **Note (Prod/Staging / CI_STRICT):**
> - When `ENV=prod|staging` or `CI_STRICT=1`, `DATABASE_URL` is **required** and **sqlite URLs are forbidden**.
> - `SYNC_DATABASE_URL` is the canonical name. Legacy `DATABASE_URL_SYNC` is kept only for backward compatibility.

1.  **Backend Setup:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Frontend Setup:**
    ```bash
    cd frontend
    yarn install
    ```

3.  **Database Preparation (Migration):**
    ```bash
    cd backend
    alembic upgrade head
    ```

4.  **Starting Services (via Supervisor):**
    In the project root:
    ```bash
    sudo supervisorctl start all
    ```
    Or manually:
    *   Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8001`
    *   Frontend: `yarn start` (Port 3000)

---

## 🧪 Testing and Verification

The system is protected by strict "Release Gates". The following tests must be run before going live:

### 1. E2E Smoke Test (Release Matrix)
Tests all critical business flows (Payments, Poker, Bonus, Risk) in one go:
```bash
python3 /app/scripts/release_smoke.py
```

### 2. Migration Check
Verifies that the database schema matches the code:
```bash
python3 /app/scripts/ci_schema_guard.py
```

### 3. Deploy Preflight
Final checks before go-live (Env vars, DB connectivity):
```bash
python3 /app/scripts/deploy_preflight.py
```

---

## 🛠️ Operational Guides (Runbooks)

Detailed procedures for critical situations can be found under `/app/artifacts/production_readiness/runbooks/`:

*   **Incident Response:** Steps to follow during system outages or attacks.
*   **Rollback Procedure:** How to revert a faulty deployment.
*   **Reconciliation Playbook:** How to resolve discrepancies between payment providers and the ledger.

### Observability
The system produces structured logs.
*   **Error Logs:** `/var/log/supervisor/backend.err.log`
*   **Access Logs:** `/var/log/supervisor/backend.out.log`
*   **Alerting:** The `AlertEngine` script runs periodically to monitor payment success rates and risk signals.

---

## 🔒 Security

*   **Immutable Ledger:** Financial records can never be deleted or updated. Only reversals can be posted.
*   **RBAC:** Admin roles (Owner, Tenant Admin, Support) are strictly separated.
*   **Audit Trail:** All admin actions are recorded in the `auditevent` table.

---

**Version:** 1.0.0 (Production Ready)
**Contact:** Ops Team
