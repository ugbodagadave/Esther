import os
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from telegram import Bot
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

async def setup_webhook():
    """Sets the Telegram webhook."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    if not RENDER_EXTERNAL_URL:
        logger.error("RENDER_EXTERNAL_URL not found in environment variables.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
    
    try:
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())
