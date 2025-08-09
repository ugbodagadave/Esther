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
        return None

def initialize_database():
    """
    Initializes the database by creating the necessary tables if they don't exist
    and adding any missing columns to existing tables.
    Creates tables in a dependency-safe order so a fresh database initializes cleanly.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1) Create wallets first (referenced by users)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS wallets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    name VARCHAR(255) NOT NULL,
                    address VARCHAR(255) UNIQUE NOT NULL,
                    encrypted_private_key TEXT NOT NULL,
                    chain_id INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Ensure chain_id column exists (backward compatibility)
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='wallets' AND column_name='chain_id'
                    ) THEN
                        ALTER TABLE wallets ADD COLUMN chain_id INTEGER DEFAULT 1;
                    END IF;
                END$$;
                """
            )

            # 2) Create users (may reference wallets)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    default_wallet_id INTEGER REFERENCES wallets(id) ON DELETE SET NULL,
                    live_trading_enabled BOOLEAN DEFAULT FALSE
                );
                """
            )

            # 3) Add missing columns to users (idempotent)
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='users' AND column_name='default_wallet_id'
                    ) THEN
                        ALTER TABLE users ADD COLUMN default_wallet_id INTEGER REFERENCES wallets(id) ON DELETE SET NULL;
                    END IF;
                END$$;
                """
            )

            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='users' AND column_name='live_trading_enabled'
                    ) THEN
                        ALTER TABLE users ADD COLUMN live_trading_enabled BOOLEAN DEFAULT FALSE;
                    END IF;
                END$$;
                """
            )

            # 4) Credentials (depends on users)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
                    encrypted_okx_api_key TEXT,
                    encrypted_okx_api_secret TEXT,
                    encrypted_okx_passphrase TEXT,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 5) Alerts (depends on users)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    symbol VARCHAR(255) NOT NULL,
                    target_price DECIMAL NOT NULL,
                    condition VARCHAR(10) NOT NULL, -- 'above' or 'below'
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 6) Portfolios (depends on users)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolios (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    last_synced TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 7) Holdings (depends on portfolios)
            cur.execute(
                """
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
                """
            )

            # 8) Prices (independent)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    price_usd NUMERIC NOT NULL
                );
                """
            )

            # 9) Portfolio history (depends on users)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    total_value_usd NUMERIC NOT NULL,
                    snapshot_date DATE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, snapshot_date)
                );
                """
            )

            # 10) Tokens metadata (independent)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    symbol VARCHAR(255) NOT NULL,
                    chain_id INTEGER NOT NULL,
                    address TEXT NOT NULL,
                    decimals INTEGER NOT NULL,
                    PRIMARY KEY(symbol, chain_id)
                );
                """
            )

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
            logger.info(f"Wallet {wallet_name} added for user {internal_user_id}.")
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

def save_portfolio_snapshot(user_id, total_value_usd):
    """Saves a daily snapshot of the user's portfolio value."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO portfolio_history (user_id, total_value_usd, snapshot_date)
                VALUES (%s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, snapshot_date) DO UPDATE SET total_value_usd = EXCLUDED.total_value_usd;
                """,
                (user_id, total_value_usd)
            )
            conn.commit()
            logger.info(f"Portfolio snapshot saved for user {user_id}.")
    except (OperationalError, psycopg2.Error) as e:
        logger.error(f"Error saving portfolio snapshot for user {user_id}: {e}")
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
