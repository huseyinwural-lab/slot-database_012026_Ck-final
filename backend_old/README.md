# Casino Admin Platform - Backend

## 🛠 Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (veya Docker ile postgres servisi)
- Supervisor (optional, for production)

### Installation

1.  **Clone the repository**
2.  **Create virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables:**
    Copy `.env.example` to `.env` and update values.
    ```bash
    cp .env.example .env
    ```

## 🚀 Running the Server

### Development (Hot Reload)
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Production (Supervisor)
Ensure supervisor is configured to run the uvicorn process.

## 📦 Database Seeding

The platform requires initial data (Tenants, Roles, Games) to function.

**1. Default Seed (Tenants & Roles):**
Runs automatically on startup.

**2. Complete Demo Data (Games, Players, Transactions):**
```bash
python -m scripts.seed_complete_data
```

## 🧪 Testing

Run unit and integration tests:
```bash
pytest
```

## 🔑 Key Features
- **Multi-Tenancy:** Single codebase, multiple isolated tenants.
- **RBAC:** Platform Owner vs Tenant Admin (Finance, Operations, Support).
- **Security:** Tenant isolation middleware, RBAC guards.
