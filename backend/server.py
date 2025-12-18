from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging
from config import settings
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.errors import AppError, app_exception_handler, generic_exception_handler

from app.core.logging_config import configure_logging

# Configure logging (env-controlled)
# Defaults: dev/local => plain, prod/staging => json
configure_logging(level=settings.log_level, fmt=settings.get_log_format())

logger = logging.getLogger(__name__)

# Fail-fast for prod/staging secrets
if settings.env in {"prod", "staging"}:
    if not settings.jwt_secret or settings.jwt_secret in {"secret", "change_this_secret_in_production_env"}:
        raise RuntimeError("JWT_SECRET must be set to a strong value in prod/staging")
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be set in prod/staging")

    # Bootstrap should not be left enabled in production.
    # We don't hard-block here to keep emergency recovery possible, but we log loudly.
    import os
    if (os.getenv("BOOTSTRAP_ENABLED") or "").lower() == "true":
        logger.warning("BOOTSTRAP_ENABLED=true in prod/staging. This should be one-shot only.")

# Create the main app
app = FastAPI(
    title="Casino Admin Panel API",
    description="Backend for Casino Admin Dashboard with AI Fraud Detection",
    version="13.0.0"
)

# Configure CORS
origins = settings.get_cors_origins()

# In prod/staging we fail-closed: CORS_ORIGINS must be explicitly set.
if settings.env in {"prod", "staging"} and (not origins or origins == ["*"]):
    raise RuntimeError("CORS_ORIGINS must be a non-wildcard allowlist in prod/staging")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (basic IP-based)
app.add_middleware(RateLimitMiddleware)

# Request logging & correlation ID (outermost middleware; runs before rate limiting)
app.add_middleware(RequestLoggingMiddleware)

# Exception Handlers
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# --- ROUTER INCLUSION (SQL ONLY) ---
# Only include routers that have been fully refactored to SQLModel
# Disabled routers are commented out to prevent legacy (pre-SQL migration) errors

# 1. Core Auth & Admin
from app.routes import auth, admin, tenant, api_keys
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tenant.router)
app.include_router(api_keys.router) 

# 2. Player Side
from app.routes import player_auth, player_lobby, player_wallet
app.include_router(player_auth.router)
app.include_router(player_lobby.router)
app.include_router(player_wallet.router)

# 3. Core Business Logic (Partially Refactored)
from app.routes import core
app.include_router(core.router)

# 4. Modules (Refactored to SQL or Stubbed)
from app.routes import fraud_detection, email_notification, simulator, modules, crm, affiliates, support, risk, approvals, rg, cms, reports, logs, version as version_router, audit as audit_router, game_config, game_import, game_config_presets, robot, revenue, finance, finance_actions, feature_flags, simulation_lab, settings as settings_router, dashboard, tables, kill_switch, flags

from app.routes import bonuses
from app.routes import kyc
app.include_router(kyc.router)
app.include_router(bonuses.router)
app.include_router(fraud_detection.router)
app.include_router(email_notification.router)
app.include_router(simulator.router)
app.include_router(modules.router)
app.include_router(crm.router)
app.include_router(affiliates.router)
app.include_router(support.router)
app.include_router(risk.router)
app.include_router(approvals.router)
app.include_router(rg.router)
app.include_router(cms.router)
app.include_router(reports.router)
app.include_router(logs.router)
app.include_router(version_router.router)
app.include_router(audit_router.router)
app.include_router(game_config.router)
app.include_router(game_import.router)
app.include_router(game_config_presets.router)
app.include_router(robot.router)
app.include_router(revenue.router)
app.include_router(finance.router)
app.include_router(finance_actions.router)
app.include_router(feature_flags.router)
app.include_router(simulation_lab.router)
app.include_router(settings_router.router)
app.include_router(dashboard.router)
app.include_router(tables.router)
app.include_router(kill_switch.router)
app.include_router(flags.router)


# Startup Event
@app.on_event("startup")
async def on_startup():
    logger.info(
        "app.startup",
        extra={
            "event": "app.startup",
            "env": settings.env,
            "log_format": settings.get_log_format(),
        },
    )
    try:
        from app.core.database import engine
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.routes.admin import seed_admin
        
        # Initialize DB
        # Prod/staging: Alembic is the single source of truth.
        # Dev/local: create_all (and optional drop_all) is allowed only under strict safety checks.
        env = settings.env

        if env in {"prod", "staging"}:
            # Migrations are executed in the container entrypoint (scripts/start_prod.sh)
            # to avoid running Alembic inside the FastAPI event loop.
            pass
        else:
            from app.core.database import init_db
            await init_db()
        
        # Seed Admin & Data (P0: guarded)
        # Fail-closed: never seed in staging/prod; in dev/local only when SEED_ON_STARTUP=true.
        if env in {"dev", "local"} and bool(settings.seed_on_startup):
            async with AsyncSession(engine) as session:
                await seed_admin(session)
            logger.info("Startup complete: Database initialized and seeded.")
        else:
            logger.info("Startup complete: Database initialized. Seeding skipped.")
    except Exception as e:
        logger.critical(f"Startup failed: {e}")

# Health Checks
@app.get("/api/health")
async def health_check():
    """Liveness probe: process up & running."""
    return {
        "status": "healthy",
        "environment": settings.env,
    }

@app.get("/api/readiness")
async def readiness_check():
    """Readiness probe: checks DB connectivity + migration state (lightweight)."""
    try:
        from app.core.database import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

            version = None
            try:
                # Migration check (lightweight): read version table.
                # - prod/staging: expected to exist after alembic upgrade head
                # - dev/local: may not exist (create_all path). In that case we do not fail readiness.
                version = (await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))).scalar() or "unknown"
            except Exception:
                if settings.env in {"prod", "staging"}:
                    raise

        return {
            "status": "ready",
            "dependencies": {
                "database": "connected",
                "migrations": "ok" if version else "unknown",
            },
            "alembic_version": version,
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("readiness check failed", exc_info=exc)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "dependencies": {"database": "unreachable", "migrations": "unknown"}},
        )


# Alias for common ops naming
@app.get("/api/ready")
async def ready_alias():
    return await readiness_check()


@app.on_event("shutdown")
async def shutdown_db_client():
    from app.core.database import engine
    logger.info("Shutting down database connection...")
    await engine.dispose()
