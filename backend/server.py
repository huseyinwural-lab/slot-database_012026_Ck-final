from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from config import settings
from app.routes import fraud_detection, email_notification, core, simulator, modules, crm, affiliates, support, risk, approvals, rg, cms, reports, logs, admin, game_config, game_import, game_config_presets, auth, api_keys, robot
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

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

# MongoDB Connection
client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.db_name]
app.state.db = db

# Configure CORS
from app.routes import dashboard

origins = settings.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
# Request logging & correlation ID
# Rate limiting (basic IP-based)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(RequestLoggingMiddleware)

    allow_headers=["*"],
)

# Include Routes
app.include_router(core.router)
app.include_router(modules.router)
app.include_router(crm.router)
app.include_router(affiliates.router)
app.include_router(support.router)
app.include_router(risk.router)
app.include_router(approvals.router)
app.include_router(rg.router)
app.include_router(cms.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(logs.router)
app.include_router(admin.router) # New Admin Router
app.include_router(fraud_detection.router)
app.include_router(email_notification.router)
app.include_router(simulator.router)
app.include_router(game_config.router)
app.include_router(game_import.router)
app.include_router(game_config_presets.router)
from app.routes import tenant
app.include_router(tenant.router)
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(robot.router)



# Finance Advanced
from app.routes import finance
app.include_router(finance.router)
# Feature Flags & A/B Testing
from app.routes import feature_flags
app.include_router(feature_flags.router)

# Simulation Lab
from app.routes import simulation_lab
app.include_router(simulation_lab.router)

# Settings Panel
from app.routes import settings as settings_router
app.include_router(settings_router.router)

# Indexes
from app.db.indexes import ensure_indexes


@app.on_event("startup")
async def init_indexes():
    await ensure_indexes(db)


@app.get("/api/health")
async def health_check():
    """Liveness probe: process up & running.

    Does NOT touch external dependencies (e.g. Mongo), so it should be cheap
    and always 200 as long as the app is alive.
    """
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


@app.get("/api/readiness")
async def readiness_check():
    """Readiness probe: checks MongoDB connectivity.

    Returns 503 if critical dependencies are not ready.
    """
    try:
        await db.command("ping")
        return {
            "status": "ready",
            "environment": settings.environment,
            "dependencies": {"mongo": "connected"},
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("readiness check failed: mongo ping error", exc_info=exc)
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail={"status": "degraded", "dependencies": {"mongo": "unreachable"}})

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
