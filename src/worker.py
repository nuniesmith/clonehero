import os
import sys
import asyncio
import signal
import requests
from loguru import logger

# Configuration
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Logging setup
LOG_FILE = "/app/logs/worker.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)  # Ensure log directory exists
logger.add(LOG_FILE, rotation="10MB", retention=5, compression="zip", level="DEBUG")

if DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG")

# Global control for worker loop
RUNNING = True

async def check_api():
    """Checks API health status with retries and exponential backoff."""
    retries = 5
    base_delay = 5  # Initial delay in seconds

    for attempt in range(retries):
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            response.raise_for_status()
            data = response.json() if "application/json" in response.headers.get("content-type", "") else response.text
            logger.info(f"✅ API Health Check: {response.status_code} - {data}")
            return True
        except requests.Timeout:
            logger.warning(f"⚠️ API Health Check Timeout (Attempt {attempt + 1}/{retries})")
        except requests.RequestException as e:
            logger.error(f"❌ API Connection Failed (Attempt {attempt + 1}/{retries}): {e}")

        # Exponential backoff
        delay = min(base_delay * (2 ** attempt), 60)  # Cap delay at 60s
        await asyncio.sleep(delay)

    logger.error("🚨 API Health Check failed after multiple attempts.")
    return False

async def worker_loop():
    """Main worker loop with controlled shutdown."""
    global RUNNING
    logger.info("🚀 Worker started...")

    while RUNNING:
        healthy = await check_api()
        retry_delay = 30 if healthy else 10  # Adjust retry delay based on API status
        await asyncio.sleep(retry_delay)

    logger.info("🛑 Worker stopped.")

def graceful_shutdown(signum, frame):
    """Handles graceful shutdown on SIGTERM/SIGINT."""
    global RUNNING
    logger.warning("⚠️ Received shutdown signal. Stopping worker...")
    RUNNING = False

# Register signal handlers for clean exit
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        logger.warning("🛑 Worker interrupted. Exiting...")
    except Exception as e:
        logger.critical(f"Unhandled exception in worker: {e}")