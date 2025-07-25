import os
import psycopg2
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        logger.error("DATABASE_URL not found in environment variables.")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the database: {e}")
        return None

def initialize_database():
    """
    Initializes the database by creating the necessary tables if they don't exist.
    """
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed. Cannot initialize tables.")
        return

    try:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create credentials table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    encrypted_okx_api_key TEXT,
                    encrypted_okx_api_secret TEXT,
                    encrypted_okx_passphrase TEXT,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully.")
    except psycopg2.Error as e:
        logger.error(f"Error initializing database tables: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Attempting to initialize the PostgreSQL database...")
    initialize_database()
    print("Database initialization script finished.")
