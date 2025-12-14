from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging
from config import settings
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.errors import AppError, app_exception_handler, generic_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(
    title="Casino Admin Panel API",
    description="Backend for Casino Admin Dashboard with AI Fraud Detection",
    version="13.0.0"
)

# Configure CORS
origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (basic IP-based)
app.add_middleware(RateLimitMiddleware)

# Exception Handlers
app.add_exception_handler(AppError, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
# Request logging & correlation ID
app.add_middleware(RequestLoggingMiddleware)

# --- ROUTER INCLUSION (SQL ONLY) ---
# Only include routers that have been fully refactored to SQLModel
# Disabled routers are commented out to prevent MongoDB errors

# 1. Core Auth & Admin
from app.routes import auth, admin, tenant, api_keys
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tenant.router)
# app.include_router(api_keys.router) # Needs Refactor

# 2. Player Side
from app.routes import player_auth, player_lobby, player_wallet
app.include_router(player_auth.router)
app.include_router(player_lobby.router)
app.include_router(player_wallet.router)

# 3. Core Business Logic (Partially Refactored)
from app.routes import core
app.include_router(core.router)

# 4. Modules (Disabled - Mongo Dependent)
# from app.routes import fraud_detection, email_notification, simulator, modules, crm, affiliates, support, risk, approvals, rg, cms, reports, logs, game_config, game_import, game_config_presets, robot, revenue, finance, finance_actions, feature_flags, simulation_lab, settings as settings_router

# Startup Event
@app.on_event("startup")
async def on_startup():
    logger.info("Application starting up...")
    try:
        from app.core.database import init_db
        from app.core.database import engine
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.routes.admin import seed_admin
        
        # Initialize DB Tables
        await init_db()
        
        # Seed Admin & Data
        async with AsyncSession(engine) as session:
            await seed_admin(session)
            
        logger.info("Startup complete: Database initialized and seeded.")
    except Exception as e:
        logger.critical(f"Startup failed: {e}")

# Health Checks
@app.get("/api/health")
async def health_check():
    """Liveness probe: process up & running."""
    return {
        "status": "healthy",
        "environment": settings.environment if hasattr(settings, 'environment') else "dev",
    }

@app.get("/api/readiness")
async def readiness_check():
    """Readiness probe: checks Database connectivity."""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "dependencies": {"database": "connected"},
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("readiness check failed: db ping error", exc_info=exc)
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"status": "degraded", "dependencies": {"database": "unreachable"}})

@app.on_event("shutdown")
async def shutdown_db_client():
    from app.core.database import engine
    logger.info("Shutting down database connection...")
    await engine.dispose()
