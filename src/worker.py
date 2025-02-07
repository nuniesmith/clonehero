import os
import time
import sys
import requests
import signal
from loguru import logger

# Configuration
API_URL = os.getenv("API_URL", "http://clonehero_api:8000")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Logging setup
logger.add("/app/logs/worker.log", rotation="10MB", retention=5, compression="zip", level="DEBUG")
if DEBUG_MODE:
    logger.add(sys.stdout, level="DEBUG")

# Global control for worker loop
RUNNING = True

def check_api():
    """Checks API health status and logs response."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json() if response.headers.get("content-type") == "application/json" else response.text
        logger.info(f"API Health Check: {response.status_code} - {data}")
    except requests.exceptions.Timeout:
        logger.error("API Health Check: Request timed out.")
    except Exception as e:
        logger.error(f"Failed to reach API: {e}")

def graceful_shutdown(signum, frame):
    """Handles graceful shutdown on SIGTERM/SIGINT."""
    global RUNNING
    logger.warning("Received shutdown signal. Stopping worker...")
    RUNNING = False

# Register signal handlers for clean exit
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

if __name__ == "__main__":
    logger.info("Worker started...")
    retry_delay = 30  # Initial retry delay (seconds)
    
    while RUNNING:
        check_api()
        time.sleep(retry_delay)