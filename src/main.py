import os
import logging
import threading
import sys
import asyncio
from pathlib import Path

# Add project root to the Python path
# This allows imports like 'from src.nlp import NLPClient' to work when the script is run from the root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Flask App for Render Health Checks ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running.", 200

# --- Telegram Bot Logic ---
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

from src.nlp import NLPClient
from src.okx_client import OKXClient
from src.database import get_db_connection

# Initialize clients
nlp_client = NLPClient()
okx_client = OKXClient()

# Global flag for simulation mode
DRY_RUN_MODE = True

# A simple, hardcoded map for common token symbols to their Ethereum addresses
TOKEN_ADDRESSES = {
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, registers the user if they don't exist."""
    user = update.effective_user
    logger.info(f"User {user.username} ({user.id}) started the bot.")
    
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Sorry, I'm having trouble connecting to the database. Please try again later.")
        return
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            result = cur.fetchone()
            
            if result is None:
                cur.execute(
                    "INSERT INTO users (telegram_id, username) VALUES (%s, %s);",
                    (user.id, user.username)
                )
                conn.commit()
                logger.info(f"New user {user.username} ({user.id}) created.")
                await update.message.reply_text("Welcome! I've created an account for you. How can I help you get started with trading on OKX DEX?")
            else:
                logger.info(f"Existing user {user.username} ({user.id}) returned.")
                await update.message.reply_text("Welcome back! How can I help you today?")
    except Exception as e:
        logger.error(f"Database error during /start for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while accessing your account.")
    finally:
        if conn:
            conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("I can help you with trading on OKX DEX. Try asking me for the price of a token, for example: 'What is the price of BTC?'")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles user messages, parses intent, and routes to the correct function."""
    user_message = update.message.text
    parsed_intent = nlp_client.parse_intent(user_message)
    
    intent = parsed_intent.get("intent")
    entities = parsed_intent.get("entities", {})

    if intent == "get_price":
        symbol = entities.get("symbol")
        if not symbol:
            await update.message.reply_text("Please specify a token symbol (e.g., BTC, ETH).")
            return
        
        from_token_address = TOKEN_ADDRESSES.get(symbol.upper())
        to_token_address = TOKEN_ADDRESSES.get("USDT")

        if not from_token_address or not to_token_address:
            await update.message.reply_text(f"Sorry, I don't have the address for the token {symbol.upper()}.")
            return

        amount_in_wei = "1000000000000000000" # 1 ETH for price check

        quote_response = okx_client.get_quote(
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount_in_wei
        )
        
        if quote_response.get("success"):
            quote_data = quote_response["data"]
            price_estimate = float(quote_data.get('toTokenAmount', 0)) / 1_000_000
            await update.message.reply_text(f"The current estimated price for {symbol.upper()}-USDT is ${price_estimate:.2f}.")
        else:
            await update.message.reply_text(f"Sorry, I couldn't fetch a quote. Error: {quote_response.get('error')}")

    elif intent == "buy_token":
        symbol = entities.get("symbol")
        amount = entities.get("amount")
        currency = entities.get("currency")

        if not all([symbol, amount, currency]):
            await update.message.reply_text("To buy a token, please tell me the amount, the token symbol, and the currency to use (e.g., 'buy 0.5 ETH with USDT').")
            return
        
        await update.message.reply_text(f"[DRY RUN] Simulating a swap of {amount} {currency.upper()} for {symbol.upper()}...")
        
        from_token_address = TOKEN_ADDRESSES.get(currency.upper())
        to_token_address = TOKEN_ADDRESSES.get(symbol.upper())

        if not from_token_address or not to_token_address:
            await update.message.reply_text(f"Sorry, I don't have the address for one of the tokens.")
            return

        # This is a huge simplification. Amount needs to be converted based on the 'from' token's decimals.
        amount_in_smallest_unit = str(int(float(amount) * 10**6)) # Assuming 6 decimals for USDC/USDT

        swap_response = okx_client.execute_swap(
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            amount=amount_in_smallest_unit,
            dry_run=DRY_RUN_MODE
        )

        if swap_response.get("success"):
            # This is a simulation, so we show the simulated result
            simulated_data = swap_response["data"]
            to_amount = float(simulated_data.get('toTokenAmount', 0)) / 10**18 # Assuming 18 decimals for ETH/WBTC
            
            response_message = (
                f"[DRY RUN] ✅ Swap Simulated Successfully!\n\n"
                f"➡️ From: {amount} {currency.upper()}\n"
                f"⬅️ To (Estimated): {to_amount:.6f} {symbol.upper()}\n\n"
                f"This was a simulation. No real transaction was executed."
            )
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(f"[DRY RUN] ❌ Simulation Failed. Error: {swap_response.get('error')}")
    
    elif intent == "greeting":
        await update.message.reply_text("Hello! How can I assist you with your trades today?")

    else:
        await update.message.reply_text("I'm not sure how to help with that. You can ask me for the price of a token.")

def run_bot():
    """Runs the Telegram bot's polling loop in a dedicated asyncio event loop."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Run the Flask app in the main thread
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask web server on port {port}...")
    app.run(host='0.0.0.0', port=port)
