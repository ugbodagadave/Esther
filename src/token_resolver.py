import logging
from src.database import get_db_connection
from src.constants import TOKEN_ADDRESSES, TOKEN_DECIMALS

logger = logging.getLogger(__name__)

class TokenResolver:
    def __init__(self):
        self.seed_tokens()

    def seed_tokens(self):
        """Seeds the tokens table with initial data from constants."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                for symbol, address in TOKEN_ADDRESSES.items():
                    if symbol == 'BTC': # Skip BTC as it's an instrument ID
                        continue
                    decimals = TOKEN_DECIMALS.get(symbol)
                    if decimals is not None:
                        cur.execute(
                            """
                            INSERT INTO tokens (symbol, chain_id, address, decimals)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (symbol, chain_id) DO NOTHING;
                            """,
                            (symbol, 1, address, decimals) # Assuming chain_id 1 for now
                        )
                conn.commit()
        except Exception as e:
            logger.error(f"Error seeding tokens: {e}")
        finally:
            if conn:
                conn.close()

    def get_token_info(self, symbol, chain_id=1):
        """Resolves token information from the database."""
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT address, decimals FROM tokens WHERE symbol = %s AND chain_id = %s;",
                    (symbol.upper(), chain_id)
                )
                result = cur.fetchone()
                if result:
                    return {"address": result[0], "decimals": result[1]}
                else:
                    return None
        except Exception as e:
            logger.error(f"Error resolving token info for {symbol}: {e}")
            return None
        finally:
            if conn:
                conn.close()
