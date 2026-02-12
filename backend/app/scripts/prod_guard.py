import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prod_guard")

async def check_db():
    url = os.getenv("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL not set")
        return False
    try:
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("DB Connection: OK")
        return True
    except Exception as e:
        logger.error(f"DB Connection Failed: {e}")
        return False

def check_env():
    required = [
        "SECRET_KEY",
        "PRAGMATIC_SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL"
    ]
    missing = []
    for r in required:
        if not os.getenv(r):
            missing.append(r)
    
    if missing:
        logger.error(f"Missing ENV: {missing}")
        return False
    
    if os.getenv("DEBUG", "false").lower() == "true":
        logger.error("DEBUG is TRUE in Production Mode")
        return False
        
    logger.info("ENV Checks: OK")
    return True

async def main():
    logger.info("Starting Production Config Guard...")
    
    checks = [
        check_env(),
        await check_db()
    ]
    
    if all(checks):
        logger.info("Guard PASS. Starting Application.")
        sys.exit(0)
    else:
        logger.critical("Guard FAIL. Aborting Startup.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
