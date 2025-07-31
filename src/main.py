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

# --- Telegram Bot Logic ---
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")

from src.nlp import NLPClient
from src.okx_client import OKXClient
from src.database import get_db_connection, initialize_database
from src.encryption import encrypt_data, decrypt_data
from src.insights import InsightsClient
from src.portfolio import PortfolioService

# Initialize clients
nlp_client = NLPClient()
okx_client = OKXClient()
insights_client = InsightsClient()
portfolio_service = PortfolioService()

# --- Conversation Handler States ---
AWAIT_CONFIRMATION = 1
AWAIT_WALLET_NAME, AWAIT_WALLET_ADDRESS, AWAIT_PRIVATE_KEY = 2, 3, 4
AWAIT_ALERT_SYMBOL, AWAIT_ALERT_CONDITION, AWAIT_ALERT_PRICE = 5, 6, 7

# Global flag for simulation mode, configurable via .env file
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "True").lower() in ("true", "1", "t")

# A simple, hardcoded map for common token symbols to their Ethereum addresses
TOKEN_ADDRESSES = {
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
}

CHAIN_ID_MAP = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, registers the user, and provides a friendly welcome."""
    user = update.effective_user
    logger.info(f"User {user.username} ({user.id}) started the bot.")

    # Keyboard for the 'What can I do?' prompt
    keyboard = [[InlineKeyboardButton("What can I do?", callback_data='help')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
                await update.message.reply_text(
                    "Hello! I'm Esther, your AI agent for navigating the world of decentralized finance.",
                    reply_markup=reply_markup
                )
            else:
                logger.info(f"Existing user {user.username} ({user.id}) returned.")
                await update.message.reply_text(
                    "Welcome back! How can I help you today?",
                    reply_markup=reply_markup
                )
    except Exception as e:
        logger.error(f"Database error during /start for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while accessing your account.")
    finally:
        if conn:
            conn.close()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued or the 'help' button is clicked."""
    help_text = (
        "Here's what I can do for you:\n\n"
        "📈 **Portfolio Management**\n"
        "   - `Show me my portfolio`: Get a full snapshot of your assets.\n"
        "   - `List my wallets`: See all your connected wallets.\n"
        "   - `Add a new wallet`: Connect a new wallet to track.\n\n"
        "💹 **Trading & Swaps**\n"
        "   - `Buy 0.1 ETH with USDC`: Execute a trade.\n"
        "   - `What is the price of BTC?`: Get the latest price for any token.\n\n"
        "🔔 **Alerts**\n"
        "   - `Set a price alert`: Get notified when a token hits your target price."
    )
    # Check if the call is from a button click
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(help_text)
    else:
        await update.message.reply_text(help_text)


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

    elif intent == "set_stop_loss":
        return await set_stop_loss_intent(update, context, entities)

    elif intent == "set_take_profit":
        return await set_take_profit_intent(update, context, entities)

    elif intent == "list_wallets":
        await list_wallets(update, context)
        return ConversationHandler.END

    elif intent == "add_wallet":
        return await add_wallet_start(update, context)

    elif intent == "show_portfolio":
        await portfolio(update, context)
        return ConversationHandler.END

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

    quote_response = okx_client.get_live_quote(
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
    source_chain = entities.get("source_chain", "ethereum").lower()
    destination_chain = entities.get("destination_chain", "ethereum").lower()

    if not all([symbol, amount, currency]):
        await update.message.reply_text("To buy a token, please tell me the amount, the token symbol, and the currency to use (e.g., 'buy 0.5 ETH with USDT').")
        return ConversationHandler.END

    from_token_address = TOKEN_ADDRESSES.get(currency.upper())
    to_token_address = TOKEN_ADDRESSES.get(symbol.upper())
    source_chain_id = CHAIN_ID_MAP.get(source_chain)
    destination_chain_id = CHAIN_ID_MAP.get(destination_chain)

    if not from_token_address or not to_token_address:
        await update.message.reply_text(f"Sorry, I don't have the address for one of the tokens.")
        return ConversationHandler.END

    if not source_chain_id or not destination_chain_id:
        await update.message.reply_text(f"Sorry, I don't support one of the specified chains.")
        return ConversationHandler.END

    # Store details in context for later use
    context.user_data['swap_details'] = {
        "from_token": currency.upper(),
        "to_token": symbol.upper(),
        "from_token_address": from_token_address,
        "to_token_address": to_token_address,
        "amount": amount,
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "source_chain_id": source_chain_id,
        "destination_chain_id": destination_chain_id,
    }

    # This is a huge simplification. Amount needs to be converted based on the 'from' token's decimals.
    amount_in_smallest_unit = str(int(float(amount) * 10**6)) # Assuming 6 decimals for USDC/USDT

    # Get a quote to show the user
    quote_response = okx_client.get_live_quote(
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        amount=amount_in_smallest_unit,
        chainId=source_chain_id
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
        f"➡️ **From:** {amount} {currency.upper()} on {source_chain.title()}\n"
        f"⬅️ **To (Estimated):** {to_amount:.6f} {symbol.upper()} on {destination_chain.title()}\n\n"
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
        chainId=swap_details['source_chain_id'],
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
    source_chain = entities.get("source_chain", "ethereum").lower()
    destination_chain = entities.get("destination_chain", "ethereum").lower()

    if not all([symbol, amount, currency]):
        await update.message.reply_text("To sell a token, please tell me the amount, the token symbol, and the currency to sell for (e.g., 'sell 0.5 ETH for USDT').")
        return ConversationHandler.END

    from_token_address = TOKEN_ADDRESSES.get(symbol.upper())
    to_token_address = TOKEN_ADDRESSES.get(currency.upper())
    source_chain_id = CHAIN_ID_MAP.get(source_chain)
    destination_chain_id = CHAIN_ID_MAP.get(destination_chain)

    if not from_token_address or not to_token_address:
        await update.message.reply_text(f"Sorry, I don't have the address for one of the tokens.")
        return ConversationHandler.END

    if not source_chain_id or not destination_chain_id:
        await update.message.reply_text(f"Sorry, I don't support one of the specified chains.")
        return ConversationHandler.END

    # Store details in context for later use
    context.user_data['swap_details'] = {
        "from_token": symbol.upper(),
        "to_token": currency.upper(),
        "from_token_address": from_token_address,
        "to_token_address": to_token_address,
        "amount": amount,
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "source_chain_id": source_chain_id,
        "destination_chain_id": destination_chain_id,
    }

    # This is a huge simplification. Amount needs to be converted based on the 'from' token's decimals.
    amount_in_smallest_unit = str(int(float(amount) * 10**18)) # Assuming 18 decimals for ETH/WBTC

    # Get a quote to show the user
    quote_response = okx_client.get_live_quote(
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        amount=amount_in_smallest_unit,
        chainId=source_chain_id
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
        f"➡️ **From:** {amount} {symbol.upper()} on {source_chain.title()}\n"
        f"⬅️ **To (Estimated):** {to_amount:.6f} {currency.upper()} on {destination_chain.title()}\n\n"
        f"This transaction will be executed on the blockchain."
    )
    
    await update.message.reply_text(response_message, reply_markup=reply_markup, parse_mode='Markdown')

    return AWAIT_CONFIRMATION

async def set_stop_loss_intent(update: Update, context: ContextTypes.DEFAULT_TYPE, entities: dict) -> int:
    """Handles the set_stop_loss intent and starts the confirmation conversation."""
    symbol = entities.get("symbol")
    price = entities.get("price")

    if not all([symbol, price]):
        await update.message.reply_text("To set a stop-loss, please tell me the token symbol and the price (e.g., 'set a stop-loss for BTC at 60000').")
        return ConversationHandler.END

    # In a real app, you would create a conditional order here.
    # For now, we will just confirm with the user.
    await update.message.reply_text(f"I've set a stop-loss for {symbol.upper()} at ${price}. I will notify you if the price drops to this level.")
    return ConversationHandler.END

async def set_take_profit_intent(update: Update, context: ContextTypes.DEFAULT_TYPE, entities: dict) -> int:
    """Handles the set_take_profit intent and starts the confirmation conversation."""
    symbol = entities.get("symbol")
    price = entities.get("price")

    if not all([symbol, price]):
        await update.message.reply_text("To set a take-profit, please tell me the token symbol and the price (e.g., 'set a take-profit for ETH at 3000').")
        return ConversationHandler.END

    # In a real app, you would create a conditional order here.
    # For now, we will just confirm with the user.
    await update.message.reply_text(f"I've set a take-profit for {symbol.upper()} at ${price}. I will notify you if the price rises to this level.")
    return ConversationHandler.END

async def insights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides personalized market insights."""
    user = update.effective_user
    await update.message.reply_text("Generating your personalized market insights... This may take a moment.")
    
    # In a real app, you would fetch the user's ID from the database
    user_id = user.id
    
    insights_text = insights_client.generate_insights(user_id)
    await update.message.reply_text(insights_text)

# --- Portfolio Command ---
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Synchronize and display the user's portfolio."""
    user = update.effective_user

    await update.message.reply_text("Syncing your portfolio... this could take a few seconds.")

    # Attempt to sync balances and check the result
    synced_ok = portfolio_service.sync_balances(user.id)
    if not synced_ok:
        await update.message.reply_text("I couldn't sync your portfolio due to an API error. Please try again later.")
        return

    snapshot = portfolio_service.get_snapshot(user.id)
    if not snapshot or not snapshot.get("assets"):
        await update.message.reply_text("Your portfolio was synced successfully, but I couldn't find any assets in your wallet(s). Have you funded your wallet yet?")
        return

    total = snapshot.get("total_value_usd", 0)
    assets = snapshot.get("assets", [])

    lines = [f"📊 *Your Portfolio* (≈ ${total:,.2f})", ""]
    for asset in assets:
        lines.append(f"• {asset['symbol']}: {asset['quantity']:.4f} (~${asset['value_usd']:.2f})")

    await update.message.reply_text("\n".join(lines), parse_mode='Markdown')

# --- Wallet Management ---
async def add_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new wallet."""
    await update.message.reply_text("Let's add a new wallet. What would you like to name it?")
    return AWAIT_WALLET_NAME

async def received_wallet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the wallet name and asks for the address."""
    context.user_data['wallet_name'] = update.message.text
    await update.message.reply_text("Got it. Now, please provide the wallet's public address.")
    return AWAIT_WALLET_ADDRESS

async def received_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the wallet address and asks for the private key."""
    context.user_data['wallet_address'] = update.message.text
    await update.message.reply_text("Great. Now, please provide the private key. This will be encrypted and stored securely.")
    return AWAIT_PRIVATE_KEY

async def received_private_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the private key, saves the wallet, and ends the conversation."""
    user = update.effective_user
    private_key = update.message.text
    wallet_name = context.user_data.get('wallet_name')
    wallet_address = context.user_data.get('wallet_address')

    encrypted_private_key = encrypt_data(private_key)

    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Database connection failed. Please try again later.")
        return ConversationHandler.END

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO wallets (user_id, name, address, encrypted_private_key) VALUES (%s, %s, %s, %s);",
                (user_id, wallet_name, wallet_address, encrypted_private_key)
            )
            conn.commit()
            await update.message.reply_text(f"✅ Wallet '{wallet_name}' added successfully!")
    except Exception as e:
        logger.error(f"Error adding wallet for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while saving your wallet.")
    finally:
        if conn:
            conn.close()
        context.user_data.clear()

    return ConversationHandler.END

async def list_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all of the user's saved wallets."""
    user = update.effective_user
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Database connection failed. Please try again later.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute("SELECT name, address FROM wallets WHERE user_id = %s;", (user_id,))
            wallets = cur.fetchall()

            if not wallets:
                await update.message.reply_text("You haven't added any wallets yet. Use /addwallet to get started.")
                return

            message = "Your saved wallets:\n\n"
            for name, address in wallets:
                message += f"🔹 **{name}**: `{address}`\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error listing wallets for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while fetching your wallets.")
    finally:
        if conn:
            conn.close()

async def delete_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the process of deleting a wallet."""
    user = update.effective_user
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Database connection failed. Please try again later.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute("SELECT name FROM wallets WHERE user_id = %s;", (user_id,))
            wallets = cur.fetchall()

            if not wallets:
                await update.message.reply_text("You don't have any wallets to delete.")
                return

            keyboard = [[InlineKeyboardButton(name[0], callback_data=f"delete_{name[0]}")] for name in wallets]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Which wallet would you like to delete?", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error starting wallet deletion for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while fetching your wallets.")
    finally:
        if conn:
            conn.close()

async def delete_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the callback for deleting a wallet."""
    query = update.callback_query
    await query.answer()
    wallet_name = query.data.split("_")[1]
    user = update.effective_user

    conn = get_db_connection()
    if conn is None:
        await query.edit_message_text("Database connection failed. Please try again later.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute("DELETE FROM wallets WHERE user_id = %s AND name = %s;", (user_id, wallet_name))
            conn.commit()
            await query.edit_message_text(f"✅ Wallet '{wallet_name}' has been deleted.")
    except Exception as e:
        logger.error(f"Error deleting wallet for user {user.id}: {e}")
        await query.edit_message_text("An error occurred while deleting your wallet.")
    finally:
        if conn:
            conn.close()

# --- Alert Management ---
async def add_alert_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new price alert."""
    await update.message.reply_text("Let's set up a price alert. Which token symbol would you like to monitor (e.g., BTC, ETH)?")
    return AWAIT_ALERT_SYMBOL

async def received_alert_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the token symbol and asks for the condition."""
    context.user_data['alert_symbol'] = update.message.text.upper()
    keyboard = [
        [
            InlineKeyboardButton("Above", callback_data="alert_above"),
            InlineKeyboardButton("Below", callback_data="alert_below"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Great. Do you want to be alerted when the price is above or below a certain value?", reply_markup=reply_markup)
    return AWAIT_ALERT_CONDITION

async def received_alert_condition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the alert condition and asks for the target price."""
    query = update.callback_query
    await query.answer()
    context.user_data['alert_condition'] = query.data.split("_")[1]
    await query.edit_message_text(text=f"Condition set to '{context.user_data['alert_condition']}'. Now, what is the target price in USD?")
    return AWAIT_ALERT_PRICE

async def received_alert_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the target price, saves the alert, and ends the conversation."""
    user = update.effective_user
    try:
        target_price = float(update.message.text)
    except ValueError:
        await update.message.reply_text("That doesn't look like a valid price. Please enter a number.")
        return AWAIT_ALERT_PRICE

    symbol = context.user_data.get('alert_symbol')
    condition = context.user_data.get('alert_condition')

    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Database connection failed. Please try again later.")
        return ConversationHandler.END

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO alerts (user_id, symbol, target_price, condition) VALUES (%s, %s, %s, %s);",
                (user_id, symbol, target_price, condition)
            )
            conn.commit()
            await update.message.reply_text(f"✅ Alert set! I will notify you when {symbol} goes {condition} ${target_price:.2f}.")
    except Exception as e:
        logger.error(f"Error adding alert for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while saving your alert.")
    finally:
        if conn:
            conn.close()
        context.user_data.clear()

    return ConversationHandler.END

async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all of the user's active alerts."""
    user = update.effective_user
    conn = get_db_connection()
    if conn is None:
        await update.message.reply_text("Database connection failed. Please try again later.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user.id,))
            user_id = cur.fetchone()[0]

            cur.execute("SELECT symbol, condition, target_price FROM alerts WHERE user_id = %s AND is_active = TRUE;", (user_id,))
            alerts = cur.fetchall()

            if not alerts:
                await update.message.reply_text("You have no active alerts. Use /addalert to create one.")
                return

            message = "Your active alerts:\n\n"
            for symbol, condition, target_price in alerts:
                message += f"🔹 **{symbol}** {condition} `${target_price:.2f}`\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error listing alerts for user {user.id}: {e}")
        await update.message.reply_text("An error occurred while fetching your alerts.")
    finally:
        if conn:
            conn.close()

# --- Bot Setup ---
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables.")

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# --- Main Conversation Handler ---
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("addwallet", add_wallet_start),
        CommandHandler("addalert", add_alert_start),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
    ],
    states={
        # States for trading conversations
        AWAIT_CONFIRMATION: [
            CallbackQueryHandler(confirm_swap, pattern="^confirm_swap$"),
            CallbackQueryHandler(cancel_swap, pattern="^cancel_swap$"),
        ],
        # States for adding a wallet
        AWAIT_WALLET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_wallet_name)],
        AWAIT_WALLET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_wallet_address)],
        AWAIT_PRIVATE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_private_key)],
        # States for adding an alert
        AWAIT_ALERT_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_alert_symbol)],
        AWAIT_ALERT_CONDITION: [CallbackQueryHandler(received_alert_condition, pattern="^alert_")],
        AWAIT_ALERT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_alert_price)],
    },
    fallbacks=[CommandHandler("start", start)],
    per_message=False,
)

application.add_handler(conv_handler)
application.add_handler(CallbackQueryHandler(help_command, pattern='^help$'))

# Add other handlers that are not part of conversations
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("insights", insights))
application.add_handler(CommandHandler("portfolio", portfolio))
application.add_handler(CommandHandler("listwallets", list_wallets))
application.add_handler(CommandHandler("listalerts", list_alerts))
application.add_handler(CommandHandler("deletewallet", delete_wallet_start))
application.add_handler(CallbackQueryHandler(delete_wallet_callback, pattern="^delete_"))


@app.route('/')
def health_check():
    return "Bot is running.", 200


@app.route('/admin/clear-database/<secret_key>', methods=['POST'])
def clear_database(secret_key):
    """(Admin) Clears and re-initializes the PostgreSQL database."""
    if not ADMIN_SECRET_KEY or secret_key != ADMIN_SECRET_KEY:
        return "Unauthorized", 401

    try:
        conn = get_db_connection()
        if conn is None:
            return "Database connection failed", 500
        
        with conn.cursor() as cur:
            # Drop all tables
            cur.execute("""
                DO $$ DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """)
        conn.commit()
        conn.close()

        # Re-initialize the schema
        initialize_database()

        return "Database cleared and re-initialized successfully.", 200
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return "An internal error occurred", 500


@app.route('/admin/clear-db-page/<secret_key>', methods=['GET'])
def show_clear_database_page(secret_key):
    """(Admin) Displays a page with a button to clear the database."""
    if not ADMIN_SECRET_KEY or secret_key != ADMIN_SECRET_KEY:
        return "Unauthorized", 401
    
    # Simple HTML page with a form that POSTs to the clear_database endpoint
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Clear Database</title>
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column; }}
            .container {{ text-align: center; border: 1px solid #ccc; padding: 30px; border-radius: 8px; }}
            button {{ background-color: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Confirm Database Clearing</h1>
            <p>Clicking this button will permanently delete all data.</p>
            <form action="/admin/clear-database/{secret_key}" method="post">
                <button type="submit">Clear Database Now</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html_content


def main() -> None:
    """Start the bot."""
    # Initialize the database first to ensure all tables and columns are created
    logger.info("Initializing database...")
    initialize_database()
    logger.info("Database initialization complete.")

    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))))
    flask_thread.daemon = True
    flask_thread.start()

    # Run the bot in polling mode
    application.run_polling()

if __name__ == "__main__":
    main()
