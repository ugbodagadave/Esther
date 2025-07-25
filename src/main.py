import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get the token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /start is issued."""
    await update.message.reply_text("Hello! I am Esther, your AI-powered trading agent. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    await update.message.reply_text("I can help you with trading on OKX DEX. Try asking me for the price of a token, for example: 'What is the price of BTC?'")

from src.nlp import NLPClient
from src.okx_client import OKXClient

# Initialize clients
nlp_client = NLPClient()
okx_client = OKXClient()

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
        
        # OKX API expects pairs like BTC-USDT
        # This is a simplification; a real implementation would need to manage the pair (e.g., default to USDT)
        trading_pair = f"{symbol.upper()}-USDT"
        
        # Note: The current OKX client gets a swap quote, not a simple price.
        # This part of the logic will need to be updated once the full swap flow is implemented.
        # For now, we'll simulate a price check.
        # A real implementation would call: okx_client.get_swap_quote(...)
        
        # Simulating a price check for now as the get_swap_quote is more complex
        # In a real scenario, you might have a different endpoint for simple price checks
        # or derive the price from the swap quote.
        
        # For Phase 1, we use the get_quote method which returns mock data.
        # This simulates getting a price without needing a real API call yet.
        # A real implementation would need to handle token addresses instead of symbols.
        quote_data = okx_client.get_quote(from_token=symbol.upper(), to_token="USDT", amount="1")
        
        if "error" in quote_data:
            await update.message.reply_text(f"Sorry, I couldn't fetch a quote. Error: {quote_data['error']}")
        else:
            await update.message.reply_text(f"The current estimated price for {quote_data['symbol']} is ${quote_data['price']}.")

    elif intent == "greeting":
        await update.message.reply_text("Hello! How can I assist you with your trades today?")
    
    else: # unknown or help
        await update.message.reply_text("I'm not sure how to help with that. You can ask me for the price of a token, like 'what is the price of BTC?'.")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - handle the message with NLP
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
