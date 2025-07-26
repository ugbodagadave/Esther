import os
import time
import logging
import asyncio
from telegram import Bot
from src.database import get_db_connection
from src.okx_client import OKXClient

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize clients
okx_client = OKXClient()
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

async def check_alerts():
    """Checks for triggered price alerts and sends notifications."""
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed. Cannot check alerts.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, user_id, symbol, target_price, condition FROM alerts WHERE is_active = TRUE;")
            alerts = cur.fetchall()

            for alert in alerts:
                alert_id, user_id, symbol, target_price, condition = alert
                
                # This is a simplified price check. In a real app, you would need to handle different quote currencies.
                from_token_address = TOKEN_ADDRESSES.get(symbol.upper())
                to_token_address = TOKEN_ADDRESSES.get("USDT")
                
                if not from_token_address or not to_token_address:
                    logger.warning(f"Skipping alert {alert_id} due to unknown symbol {symbol}")
                    continue

                quote_response = okx_client.get_live_quote(
                    from_token_address=from_token_address,
                    to_token_address=to_token_address,
                    amount="1000000000000000000" # 1 ETH for price check
                )

                if quote_response.get("success"):
                    current_price = float(quote_response["data"].get('toTokenAmount', 0)) / 1_000_000
                    
                    if (condition == 'above' and current_price > target_price) or \
                       (condition == 'below' and current_price < target_price):
                        
                        message = f"🚨 Price Alert! {symbol} is now ${current_price:.2f}, which is {condition} your target of ${target_price:.2f}."
                        await bot.send_message(chat_id=user_id, text=message)
                        
                        # Deactivate the alert after it has been triggered
                        cur.execute("UPDATE alerts SET is_active = FALSE WHERE id = %s;", (alert_id,))
                        conn.commit()
                        logger.info(f"Triggered and deactivated alert {alert_id} for user {user_id}")

    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
    finally:
        if conn:
            conn.close()

async def main():
    """Main loop for the monitoring service."""
    while True:
        logger.info("Checking for price alerts...")
        await check_alerts()
        await asyncio.sleep(60) # Check every 60 seconds

if __name__ == '__main__':
    # This is a placeholder for the TOKEN_ADDRESSES map. In a real implementation, this would be shared.
    TOKEN_ADDRESSES = {
        "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    }
    asyncio.run(main())
