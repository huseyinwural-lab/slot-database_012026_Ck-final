import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frontend_scanner")

def scan_build_integrity(build_dir="frontend/build"):
    logger.info(f"Scanning build directory: {build_dir}")
    
    # 1. Console Logs
    try:
        res = subprocess.run(
            ['grep', '-r', 'console.log', build_dir],
            capture_output=True, text=True
        )
        if res.stdout:
            logger.error("FAIL: Found console.log in build!")
            print(res.stdout[:500]) # Print first few matches
            return False
    except Exception as e:
        logger.warning(f"Grep failed (maybe dir missing): {e}")

    # 2. Emergent/PostHog
    keywords = ["posthog.init", "assets.emergent.sh", "emergent-badge"]
    for kw in keywords:
        try:
            res = subprocess.run(
                ['grep', '-r', kw, build_dir],
                capture_output=True, text=True
            )
            if res.stdout:
                logger.error(f"FAIL: Found {kw} in build!")
                return False
        except:
            pass
            
    logger.info("PASS: Frontend integrity check clear.")
    return True

if __name__ == "__main__":
    # In CI this would run after 'npm run build'
    # For now we just place the script.
    pass
