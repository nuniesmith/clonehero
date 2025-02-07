import os
import psycopg2
from psycopg2 import pool, OperationalError, errors
from loguru import logger
from contextlib import contextmanager

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "clonehero_db"),
    "database": os.getenv("DB_NAME", "clonehero"),
    "user": os.getenv("DB_USER", "clonehero"),
    "password": os.getenv("DB_PASS", "clonehero"),
    "port": os.getenv("DB_PORT", "5432"),
}

# Connection Pool
try:
    db_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        **DB_CONFIG
    )
    logger.info("✅ Database connection pool initialized successfully.")
except Exception as e:
    logger.critical(f"❌ Failed to initialize database pool: {e}")
    db_pool = None  # Prevent errors when calling get_connection()

@contextmanager
def get_connection():
    """Context manager for safely acquiring and releasing a database connection."""
    if db_pool is None:
        logger.error("Database pool is not initialized.")
        raise RuntimeError("Database pool is unavailable.")
    
    conn = None
    try:
        conn = db_pool.getconn()
        logger.debug("🔗 Database connection acquired.")
        yield conn
    except OperationalError as e:
        logger.error(f"⚠️ Database connection error: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)
            logger.debug("🔓 Database connection released.")

def execute_sql_file(sql_file: str):
    """Executes an SQL file with better error handling."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor, open(sql_file, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
            conn.commit()
            logger.info(f"✅ Successfully executed SQL file: {sql_file}")
    except (OperationalError, errors.DatabaseError) as e:
        logger.error(f"❌ Error executing SQL file {sql_file}: {e}")

def init_db():
    """Initializes the database schema and triggers."""
    logger.info("🚀 Initializing database...")
    execute_sql_file("/app/src/sql/schema.sql")
    execute_sql_file("/app/src/sql/triggers.sql")
    logger.success("🎉 Database initialization completed successfully.")

if __name__ == "__main__":
    init_db()