from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from config import settings
from app.routes import fraud_detection, email_notification, core, simulator, modules, crm, affiliates, support, risk, approvals

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
    version="8.0.0"
)

# MongoDB Connection
client = AsyncIOMotorClient(settings.mongo_url)
db = client[settings.db_name]
app.state.db = db

# Configure CORS
origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(core.router)
app.include_router(modules.router)
app.include_router(crm.router)
app.include_router(affiliates.router)
app.include_router(support.router)
app.include_router(risk.router)
app.include_router(approvals.router) # New Approvals Router
app.include_router(fraud_detection.router)
app.include_router(email_notification.router)
app.include_router(simulator.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "db": "connected" if await db.command("ping") else "disconnected"
    }

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
