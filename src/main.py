import os
import sys
import asyncio
import random
import time
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from loguru import logger
from psycopg2 import OperationalError, errors

# Ensure the module can be found by adding its root directory to `sys.path`
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import DB init function
from src.database import init_db

# Import routers
from src.routes.upload_content import router as upload_router
from src.routes.song_processing import router as song_processing_router
from src.routes.song_upload import router as song_upload_router
from src.routes.health import router as health_router
from src.routes.database_explorer import router as database_explorer_router

# Ensure logs directory exists before setting up logging
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure Loguru logging (logging to file and console)
LOG_FILE = os.path.join(LOG_DIR, "app.log")
logger.add(LOG_FILE, rotation="10MB", retention="7 days", level="DEBUG")
logger.add(sys.stdout, level="INFO")

async def wait_for_db(max_retries=10, base_delay=5):
    """Wait for the database to be ready before initializing."""
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Attempting DB connection ({attempt + 1}/{max_retries})...")
            init_db()  # Directly call init_db() instead of using asyncio.to_thread()
            logger.success("✅ Database initialized successfully.")
            return
        except (OperationalError, errors.DatabaseError) as e:
            delay_time = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60)
            logger.warning(f"⚠️ Database not ready. Retrying in {delay_time:.2f}s - {e}")
            await asyncio.sleep(delay_time)
        except Exception as e:
            logger.critical(f"❌ Unexpected error while connecting to DB: {e}")
            return  # Don't exit, just fail gracefully
    
    logger.error("❌ Database connection failed after multiple attempts.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensures database is initialized before the app starts and handles cleanup on shutdown."""
    await wait_for_db()
    yield  # Application runs here
    logger.info("🛑 FastAPI application is shutting down...")

def create_app() -> FastAPI:
    """Creates the FastAPI application with middleware and routes."""
    app = FastAPI(lifespan=lifespan)

    # Middleware for logging requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        logger.info(f"📥 Incoming request: {request.method} {request.url}")
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"❌ Unhandled error: {e}")
            raise e
        finally:
            duration = round(time.time() - start_time, 3)
            logger.info(f"📤 {request.method} {request.url} - {response.status_code} [{duration}s]")
        return response

    # Register API routes
    routers = [
        upload_router,
        health_router,
        database_explorer_router,
        song_processing_router,
        song_upload_router,
    ]
    for router in routers:
        app.include_router(router, prefix="")

    return app

# Create and run the FastAPI application
app = create_app()