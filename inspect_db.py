import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

load_dotenv()

from src.database import get_db_connection

def inspect_database():
    """Connects to the database and prints the contents of the users and wallets tables."""
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cur:
            print("--- Users ---")
            cur.execute("SELECT * FROM users;")
            users = cur.fetchall()
            for user in users:
                print(user)

            print("\n--- Wallets ---")
            cur.execute("SELECT * FROM wallets;")
            wallets = cur.fetchall()
            for wallet in wallets:
                print(wallet)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_database()
