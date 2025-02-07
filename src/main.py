import os
import sys
import asyncio
import random
from fastapi import FastAPI, Request, UploadFile, File
from contextlib import asynccontextmanager
from loguru import logger
from psycopg2 import OperationalError, errors

# Ensure the module can be found by adding its root directory to `sys.path`
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import DB init function
from src.database import init_db

# Import routers
from src.routes.upload import router as upload_router
from src.routes.song_processing import router as song_processing_router
from src.routes.song_upload import router as song_upload_router
from src.routes.health import router as health_router
from src.routes.database_explorer import router as database_explorer_router

# Ensure logs directory exists before setting up logging
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure Loguru logging (logging to file and console)
LOG_FILE = os.path.join(LOG_DIR, "app.log")
logger.add(LOG_FILE, rotation="10MB", retention="7 days", level="DEBUG")
logger.add(sys.stdout, level="INFO")

async def wait_for_db():
    """Wait for the database to be ready before initializing."""
    retries = 10
    base_delay = 5  # seconds
    for attempt in range(retries):
        try:
            logger.info(f"🔄 Attempting DB connection ({attempt + 1}/{retries})...")
            init_db()  # Directly call init_db() instead of using asyncio.to_thread()
            logger.info("✅ Database initialized successfully.")
            return
        except (OperationalError, errors.DatabaseError) as e:
            delay_time = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60)
            logger.warning(f"⚠️ Database not ready. Retrying in {delay_time:.2f}s - {e}")
            await asyncio.sleep(delay_time)
        except Exception as e:
            logger.error(f"❌ Unexpected error while connecting to DB: {e}")
            sys.exit(1)
    
    logger.error("❌ Database connection failed after multiple attempts. Exiting...")
    sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensures database is initialized before the app starts."""
    await wait_for_db()
    yield

def create_app() -> FastAPI:
    """Creates the FastAPI application with middleware and routes."""
    app = FastAPI(lifespan=lifespan)

    # Middleware for logging requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"📥 Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"📤 Response status: {response.status_code}")
        return response

    # Include routers
    app.include_router(upload_router, prefix="", tags=["Upload"])
    app.include_router(health_router, prefix="", tags=["Health"])
    app.include_router(database_explorer_router, prefix="", tags=["Database Explorer"])
    app.include_router(song_processing_router, prefix="", tags=["Song Processing"])
    app.include_router(song_upload_router, prefix="", tags=["Song Upload"])

    return app

# Create and run the FastAPI application
app = create_app()