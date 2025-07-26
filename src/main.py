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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
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
from src.encryption import encrypt_data, decrypt_data

# Initialize clients
nlp_client = NLPClient()
okx_client = OKXClient()

# --- Conversation Handler States ---
AWAIT_CONFIRMATION = 1
AWAIT_WALLET_NAME, AWAIT_WALLET_ADDRESS, AWAIT_PRIVATE_KEY = 2, 3, 4

# Global flag for simulation mode, configurable via .env file
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "True").lower() in ("true", "1", "t")

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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles regular text messages, parses intent, and initiates actions."""
    user_message = update.message.text
    parsed_intent = nlp_client.parse_intent(user_message)
    
    intent = parsed_intent.get("intent")
    entities = parsed_intent.get("entities", {})

    if intent == "get_price":
        await get_price_intent(update, context, entities)
        return ConversationHandler.END

    elif intent == "buy_token":
        return await buy_token_intent(update, context, entities)

    elif intent == "sell_token":
        return await sell_token_intent(update, context, entities)

    elif intent == "greeting":
        await update.message.reply_text("Hello! How can I assist you with your trades today?")
        return ConversationHandler.END

    else:
        await update.message.reply_text("I'm not sure how to help with that. You can ask me for the price of a token or to buy a token.")
        return ConversationHandler.END

async def get_price_intent(update: Update, context: ContextTypes.DEFAULT_TYPE, entities: dict):
    """Handles the get_price intent."""
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

async def buy_token_intent(update: Update, context: ContextTypes.DEFAULT_TYPE, entities: dict) -> int:
    """Handles the buy_token intent and starts the confirmation conversation."""
    symbol = entities.get("symbol")
    amount = entities.get("amount")
    currency = entities.get("currency")

    if not all([symbol, amount, currency]):
        await update.message.reply_text("To buy a token, please tell me the amount, the token symbol, and the currency to use (e.g., 'buy 0.5 ETH with USDT').")
        return ConversationHandler.END

    from_token_address = TOKEN_ADDRESSES.get(currency.upper())
    to_token_address = TOKEN_ADDRESSES.get(symbol.upper())

    if not from_token_address or not to_token_address:
        await update.message.reply_text(f"Sorry, I don't have the address for one of the tokens.")
        return ConversationHandler.END

    # Store details in context for later use
    context.user_data['swap_details'] = {
        "from_token": currency.upper(),
        "to_token": symbol.upper(),
        "from_token_address": from_token_address,
        "to_token_address": to_token_address,
        "amount": amount,
    }

    # This is a huge simplification. Amount needs to be converted based on the 'from' token's decimals.
    amount_in_smallest_unit = str(int(float(amount) * 10**6)) # Assuming 6 decimals for USDC/USDT

    # Get a quote to show the user
    quote_response = okx_client.get_quote(
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        amount=amount_in_smallest_unit
    )

    if not quote_response.get("success"):
        await update.message.reply_text(f"Sorry, I couldn't get a quote for that swap. Error: {quote_response.get('error')}")
        return ConversationHandler.END

    quote_data = quote_response["data"]
    to_amount = float(quote_data.get('toTokenAmount', 0)) / 10**18 # Assuming 18 decimals for ETH/WBTC

    context.user_data['swap_details']['amount_in_smallest_unit'] = amount_in_smallest_unit
    context.user_data['swap_details']['estimated_to_amount'] = to_amount

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_swap"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_swap"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response_message = (
        f"Please confirm the following swap:\n\n"
        f"➡️ **From:** {amount} {currency.upper()}\n"
        f"⬅️ **To (Estimated):** {to_amount:.6f} {symbol.upper()}\n\n"
        f"This transaction will be executed on the blockchain."
    )
    
    await update.message.reply_text(response_message, reply_markup=reply_markup, parse_mode='Markdown')

    return AWAIT_CONFIRMATION

async def confirm_swap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Executes the swap after user confirmation."""
    query = update.callback_query
    await query.answer()
    
    swap_details = context.user_data.get('swap_details')
    if not swap_details:
        await query.edit_message_text(text="Sorry, the swap details have expired. Please try again.")
        return ConversationHandler.END

    # In a real app, you would fetch this from the user's profile in the database
    wallet_address = os.getenv("TEST_WALLET_ADDRESS", "0xYourDefaultWalletAddress")

    await query.edit_message_text(text=f"Executing swap of {swap_details['amount']} {swap_details['from_token']} for {swap_details['to_token']}...")

    swap_response = okx_client.execute_swap(
        from_token_address=swap_details['from_token_address'],
        to_token_address=swap_details['to_token_address'],
        amount=swap_details['amount_in_smallest_unit'],
        wallet_address=wallet_address,
        dry_run=DRY_RUN_MODE
    )

    if swap_response.get("success"):
        response_data = swap_response["data"]
        to_amount = float(response_data.get('toTokenAmount', 0)) / 10**18 # Assuming 18 decimals for ETH/WBTC
        
        status_message = "✅ Swap Simulated Successfully!" if DRY_RUN_MODE else "✅ Swap Executed Successfully!"
        
        response_message = (
            f"[{'DRY RUN' if DRY_RUN_MODE else 'LIVE'}] {status_message}\n\n"
            f"➡️ From: {swap_details['amount']} {swap_details['from_token']}\n"
            f"⬅️ To (Actual): {to_amount:.6f} {swap_details['to_token']}\n\n"
        )
        if DRY_RUN_MODE:
            response_message += "This was a simulation. No real transaction was executed."
        else:
            tx_hash = response_data.get('txHash', 'N/A')
            response_message += f"Transaction Hash: `{tx_hash}`"

        await query.edit_message_text(text=response_message, parse_mode='Markdown')
    else:
        status_message = "❌ Simulation Failed" if DRY_RUN_MODE else "❌ Swap Failed"
        await query.edit_message_text(text=f"[{'DRY RUN' if DRY_RUN_MODE else 'LIVE'}] {status_message}. Error: {swap_response.get('error')}")

    context.user_data.pop('swap_details', None)
    return ConversationHandler.END

async def cancel_swap(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the swap conversation."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Swap cancelled.")
    context.user_data.pop('swap_details', None)
    return ConversationHandler.END

async def sell_token_intent(update: Update, context: ContextTypes.DEFAULT_TYPE, entities: dict) -> int:
    """Handles the sell_token intent and starts the confirmation conversation."""
    symbol = entities.get("symbol")
    amount = entities.get("amount")
    currency = entities.get("currency")

    if not all([symbol, amount, currency]):
        await update.message.reply_text("To sell a token, please tell me the amount, the token symbol, and the currency to sell for (e.g., 'sell 0.5 ETH for USDT').")
        return ConversationHandler.END

    from_token_address = TOKEN_ADDRESSES.get(symbol.upper())
    to_token_address = TOKEN_ADDRESSES.get(currency.upper())

    if not from_token_address or not to_token_address:
        await update.message.reply_text(f"Sorry, I don't have the address for one of the tokens.")
        return ConversationHandler.END

    # Store details in context for later use
    context.user_data['swap_details'] = {
        "from_token": symbol.upper(),
        "to_token": currency.upper(),
        "from_token_address": from_token_address,
        "to_token_address": to_token_address,
        "amount": amount,
    }

    # This is a huge simplification. Amount needs to be converted based on the 'from' token's decimals.
    amount_in_smallest_unit = str(int(float(amount) * 10**18)) # Assuming 18 decimals for ETH/WBTC

    # Get a quote to show the user
    quote_response = okx_client.get_quote(
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        amount=amount_in_smallest_unit
    )

    if not quote_response.get("success"):
        await update.message.reply_text(f"Sorry, I couldn't get a quote for that swap. Error: {quote_response.get('error')}")
        return ConversationHandler.END

    quote_data = quote_response["data"]
    to_amount = float(quote_data.get('toTokenAmount', 0)) / 10**6 # Assuming 6 decimals for USDC/USDT

    context.user_data['swap_details']['amount_in_smallest_unit'] = amount_in_smallest_unit
    context.user_data['swap_details']['estimated_to_amount'] = to_amount

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_swap"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_swap"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response_message = (
        f"Please confirm the following swap:\n\n"
        f"➡️ **From:** {amount} {symbol.upper()}\n"
        f"⬅️ **To (Estimated):** {to_amount:.6f} {currency.upper()}\n\n"
        f"This transaction will be executed on the blockchain."
    )
    
    await update.message.reply_text(response_message, reply_markup=reply_markup, parse_mode='Markdown')

    return AWAIT_CONFIRMATION

def run_bot():
    """Runs the Telegram bot's polling loop in a dedicated asyncio event loop."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Conversation Handlers ---
    swap_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
        states={
            AWAIT_CONFIRMATION: [
                CallbackQueryHandler(confirm_swap, pattern="^confirm_swap$"),
                CallbackQueryHandler(cancel_swap, pattern="^cancel_swap$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
    )

    add_wallet_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addwallet", add_wallet_start)],
        states={
            AWAIT_WALLET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_wallet_name)],
            AWAIT_WALLET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_wallet_address)],
            AWAIT_PRIVATE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_private_key)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(swap_conv_handler)
    application.add_handler(add_wallet_conv_handler)
    application.add_handler(CallbackQueryHandler(delete_wallet_callback, pattern="^delete_"))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addwallet", add_wallet_start))
    application.add_handler(CommandHandler("listwallets", list_wallets))
    application.add_handler(CommandHandler("deletewallet", delete_wallet_start))
    
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
