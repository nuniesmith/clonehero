from psycopg2 import pool, OperationalError, errors
from loguru import logger
import os

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "clonehero_db")
DB_NAME = os.getenv("DB_NAME", "clonehero")
DB_USER = os.getenv("DB_USER", "clonehero")
DB_PASS = os.getenv("DB_PASS", "clonehero")
DB_PORT = os.getenv("DB_PORT", "5432")

# Connection Pool
db_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    port=DB_PORT
)

def get_connection():
    """Gets a connection from the connection pool."""
    try:
        conn = db_pool.getconn()
        logger.info("Database connection acquired.")
        return conn
    except Exception as e:
        logger.error(f"Database connection pool error: {e}")
        raise

def release_connection(conn):
    """Returns a connection back to the pool."""
    if conn:
        db_pool.putconn(conn)
        logger.info("Database connection released.")

def execute_sql_file(sql_file: str):
    """Executes an SQL file."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        with open(sql_file, "r") as f:
            cursor.execute(f.read())
        conn.commit()
        cursor.close()
        logger.info(f"Executed SQL file: {sql_file}")
    except (OperationalError, errors.DatabaseError) as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing SQL file {sql_file}: {e}")
    finally:
        if conn:
            release_connection(conn)

def init_db():
    """Initializes the database schema."""
    execute_sql_file("/app/src/sql/schema.sql")
    execute_sql_file("/app/src/sql/triggers.sql")
    logger.info("Database initialized successfully.")

if __name__ == "__main__":
    init_db()