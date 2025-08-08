import os
import psycopg2
import logging
from dotenv import load_dotenv
from src.exceptions import WalletAlreadyExistsError, DatabaseConnectionError
from psycopg2 import OperationalError, IntegrityError

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
        raise DatabaseConnectionError("DATABASE_URL not found in environment variables.")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except OperationalError as e:
        logger.error(f"Could not connect to the database: {e}")
        raise DatabaseConnectionError(f"Could not connect to the database: {e}")

def initialize_database():
    """
    Initializes the database by creating the necessary tables if they don't exist
    and adding any missing columns to existing tables.
    """
    try:
        conn = get_db_connection()
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

            # Create wallets table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    name VARCHAR(255) NOT NULL,
                    address VARCHAR(255) UNIQUE NOT NULL,
                    encrypted_private_key TEXT NOT NULL,
                    chain_id INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Add chain_id to wallets table if it doesn't exist (for backward compatibility)
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='wallets' AND column_name='chain_id'
                    ) THEN
                        ALTER TABLE wallets ADD COLUMN chain_id INTEGER DEFAULT 1;
                    END IF;
                END$$;
            """)

            # Create alerts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    symbol VARCHAR(255) NOT NULL,
                    target_price DECIMAL NOT NULL,
                    condition VARCHAR(10) NOT NULL, -- 'above' or 'below'
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create portfolios table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    last_synced TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create holdings table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    id SERIAL PRIMARY KEY,
                    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
                    chain_id INTEGER,
                    token_address TEXT,
                    symbol VARCHAR(255),
                    amount NUMERIC,
                    decimals INTEGER,
                    value_usd NUMERIC,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create prices table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    price_usd NUMERIC NOT NULL
                );
            """)
            
            conn.commit()
            logger.info("Database tables initialized successfully.")
    except (OperationalError, psycopg2.Error) as e:
        logger.error(f"Error initializing database tables: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def add_wallet(user_id, wallet_name, wallet_address, encrypted_private_key, chain_id=1):
    """Adds a new wallet to the database for a given user."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get the internal user ID from the telegram_id
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user_id,))
            user_record = cur.fetchone()
            if not user_record:
                # If the user doesn't exist, create a new one
                cur.execute("INSERT INTO users (telegram_id) VALUES (%s) RETURNING id;", (user_id,))
                user_record = cur.fetchone()
            
            internal_user_id = user_record[0]

            cur.execute(
                """
                INSERT INTO wallets (user_id, name, address, encrypted_private_key, chain_id)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (internal_user_id, wallet_name, wallet_address, encrypted_private_key, chain_id)
            )
            conn.commit()
            logger.info(f"Wallet {wallet_name} added for user {user_id}.")
    except IntegrityError as e:
        if e.pgcode == '23505': # unique_violation
            raise WalletAlreadyExistsError(f"Wallet with address {wallet_address} already exists.")
        else:
            raise e
    except (OperationalError, psycopg2.Error) as e:
        logger.error(f"Error adding wallet for user {user_id}: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Attempting to initialize the PostgreSQL database...")
    initialize_database()
    print("Database initialization script finished.")
