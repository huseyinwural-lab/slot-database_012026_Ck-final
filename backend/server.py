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

# P0.8: Fail-fast DB/Redis config guard
# - In prod/staging OR CI_STRICT=1 -> DATABASE_URL must be set.
# - SQLite DB URLs are forbidden in these environments.
# - Redis is OPTIONAL in prod/staging unless REDIS_REQUIRED=true.
import os
from pathlib import Path
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory


from app.core.redis_health import redis_ping

from sqlalchemy.engine.url import make_url

is_ci_strict = (os.getenv("CI_STRICT") or "").strip().lower() in {"1", "true", "yes"}

def _is_sqlite_url(url: str) -> bool:
    try:
        driver = make_url(url).drivername
    except Exception:
        return False
    return driver.startswith("sqlite")


async def _redis_connectable(redis_url: str) -> bool:
    try:
        return await redis_ping(redis_url)
    except Exception:
        return False


if settings.env in {"prod", "staging"} or is_ci_strict:
    # Ensure this is not silently falling back to config defaults.
    if not (os.getenv("DATABASE_URL") or "").strip():
        raise RuntimeError("DATABASE_URL must be set (prod/staging or CI_STRICT)")
    if _is_sqlite_url(settings.database_url):
        raise RuntimeError("SQLite DATABASE_URL is not allowed in prod/staging or CI_STRICT")

    # Redis is optional unless explicitly required.
    if bool(getattr(settings, "redis_required", False)):
        if not (os.getenv("REDIS_URL") or "").strip():
            raise RuntimeError("REDIS_URL must be set when REDIS_REQUIRED=true")
        # Reachability is validated at readiness.

# Fail-fast for prod/staging secrets
if settings.env in {"prod", "staging"}:
    if not settings.jwt_secret or settings.jwt_secret in {"secret", "change_this_secret_in_production_env"}:
        raise RuntimeError("JWT_SECRET must be set to a strong value in prod/staging")

    # Bootstrap should not be left enabled in production.
    # We don't hard-block here to keep emergency recovery possible, but we log loudly.
    if (os.getenv("BOOTSTRAP_ENABLED") or "").lower() == "true":
        logger.warning("BOOTSTRAP_ENABLED=true in prod/staging. This should be one-shot only.")

# Create the main app
app = FastAPI(
    title="Casino Admin Panel API",
    description="Backend for Casino Admin Dashboard with AI Fraud Detection",
    version="13.0.0"
)

# P0-1: Run secret validation on startup
settings.validate_prod_secrets()

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
# Request Context (Task 4)
from app.middleware.request_context import RequestContextMiddleware
app.add_middleware(RequestContextMiddleware)
# Metrics Middleware
from app.middleware.metrics_middleware import MetricsMiddleware
app.add_middleware(MetricsMiddleware)

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
from app.routes import payouts
app.include_router(payouts.router)
from app.routes import player_ops
app.include_router(player_ops.router)

# 3. Core Business Logic (Partially Refactored)
from app.routes import core
app.include_router(core.router)

# Admin ledger/manual adjustments (P1-B-S: PSP-free money-loop smoke)
from app.routes import ledger_admin
app.include_router(ledger_admin.router)

from app.routes import payments
app.include_router(payments.router)

from app.routes import stripe_payments
app.include_router(stripe_payments.router)

from app.routes import adyen_payments
app.include_router(adyen_payments.router)
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
from app.routes import robots, math_assets
from app.routes import admin_payments
app.include_router(admin_payments.router)
from app.routes import rg
app.include_router(rg.router)
from app.routes import poker_mtt
app.include_router(poker_mtt.router)
from app.routes.integrations import poker
app.include_router(poker.router)
from app.routes import bonuses
app.include_router(bonuses.router)
from app.routes import vip
app.include_router(vip.router)
from app.routes import engine
app.include_router(engine.router)
app.include_router(robots.router)
app.include_router(math_assets.router)
app.include_router(revenue.router)
from app.routes import finance_refunds
app.include_router(finance_refunds.router)
app.include_router(finance.router)
from app.routes import finance_chargebacks
from app.routes import rg_player
from app.routes import games_integration
from app.routes import mock_provider
from app.routes import games_client
app.include_router(games_client.router)
app.include_router(mock_provider.router)
app.include_router(games_integration.router)
app.include_router(rg_player.router)
app.include_router(finance_chargebacks.router)
app.include_router(finance_actions.router)
app.include_router(feature_flags.router)
app.include_router(simulation_lab.router)
app.include_router(settings_router.router)
app.include_router(dashboard.router)
app.include_router(tables.router)
app.include_router(kill_switch.router)
from app.routes import ops
app.include_router(ops.router)
app.include_router(flags.router)
from app.routes import risk_admin
app.include_router(risk_admin.router)
from app.routes import offer_admin
app.include_router(offer_admin.router)
from app.routes import dispute_admin
app.include_router(dispute_admin.router)
from app.routes import poker_mtt_player
app.include_router(poker_mtt_player.router)
from app.routes import reconciliation as reconciliation_router
app.include_router(reconciliation_router.router)

from app.routes import ci_seed
app.include_router(ci_seed.router)




# Startup Event
@app.on_event("startup")
async def on_startup():
    from app.core.build_info import get_build_info

    logger.info(
        "service.boot",
        extra={
            "event": "service.boot",
            **get_build_info(service="backend"),
            "env": settings.env,
            "log_format": settings.get_log_format(),
        },
    )

    # P0.7: Config snapshot (NO secrets). Helps debug connection issues quickly.
    try:
        from app.core.connection_strings import summarize_database_url, summarize_redis_url

        logger.info(
            "config.snapshot",
            extra={
                "event": "config.snapshot",
                "db": summarize_database_url(settings.database_url),
                "redis": summarize_redis_url(settings.redis_url),
            },
        )
    except Exception:
        # Best effort; don't block startup.
        pass

    try:
        from app.core.database import engine
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.routes.admin import seed_admin
        from app.queue.arq_client import init_queue
        
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

        # Initialise ARQ queue only when explicitly configured
        if settings.recon_runner == "queue":
            try:
                await init_queue()
                logger.info("Reconciliation ARQ queue initialised.")
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Failed to initialise ARQ queue", exc_info=exc)
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
    """Readiness probe: checks DB connectivity + migration state.

    IMPORTANT: In prod/staging/ci we must not return READY if DB alembic_version is
    behind local migration head.

    If REDIS_REQUIRED=true, Redis is treated as a CRITICAL dependency.
    """
    try:
        from app.core.database import engine
        from sqlalchemy import text

        def _local_alembic_head() -> str:
            # Load alembic config from backend/alembic.ini
            here = Path(__file__).resolve().parent
            alembic_ini = str(here / "alembic.ini")
            cfg = AlembicConfig(alembic_ini)
            cfg.set_main_option("script_location", "alembic")
            script = ScriptDirectory.from_config(cfg)
            heads = list(script.get_heads())
            return heads[0] if heads else "unknown"

        expected_head = _local_alembic_head()

        # DB check
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

            db_version = None
            try:
                db_version = (await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))).scalar() or "unknown"
            except Exception:
                # dev/local may not have alembic_version; do not fail readiness there
                if settings.env in {"prod", "staging", "ci"}:
                    raise

        # Strict migration comparison in prod/staging/ci
        migrations_status = "unknown"
        if db_version and expected_head and db_version != "unknown" and expected_head != "unknown":
            migrations_status = "ok" if db_version == expected_head else "behind"

        if settings.env in {"prod", "staging", "ci"} and migrations_status == "behind":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=503,
                detail={
                    "status": "degraded",
                    "dependencies": {
                        "database": "connected",
                        "redis": "unknown",
                        "migrations": "behind",
                    },
                    "alembic": {"db": db_version, "head": expected_head},
                },
            )

        # Redis check (critical only when explicitly required)
        redis_status = "skipped"
        if bool(getattr(settings, "redis_required", False)):
            redis_status = "connected" if await _redis_connectable(settings.redis_url) else "unreachable"
            if redis_status != "connected":
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=503,
                    detail={
                        "status": "degraded",
                        "dependencies": {"database": "connected", "redis": "unreachable", "migrations": migrations_status},
                        "alembic": {"db": db_version, "head": expected_head},
                    },
                )

        return {
            "status": "ready",
            "dependencies": {
                "database": "connected",
                "redis": redis_status,
                "migrations": migrations_status,
            },
            "alembic": {"db": db_version, "head": expected_head},
        }
    except Exception as exc:  # pragma: no cover - defensive
        # Pass through HTTPException as-is
        from fastapi import HTTPException

        if isinstance(exc, HTTPException):
            raise

        logger.exception("readiness check failed", exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "dependencies": {"database": "unreachable", "redis": "unknown", "migrations": "unknown"}},
        )


@app.on_event("shutdown")
async def on_shutdown():
    from app.queue.arq_client import close_queue

    try:
        await close_queue()
    except Exception:
        # Best-effort cleanup; don't block shutdown
        pass


# Alias for common ops naming
@app.get("/api/ready")
async def ready_alias():
    return await readiness_check()


@app.on_event("shutdown")
async def shutdown_db_client():
    from app.core.database import engine
    logger.info("Shutting down database connection...")
    await engine.dispose()
