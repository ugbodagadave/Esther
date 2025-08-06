import threading
import uvicorn
from src.main import app, application

def start_bot():
    """Starts the Telegram bot with polling."""
    application.run_polling()

def start_flask():
    """Starts the Flask app."""
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    # Start the Flask app in the main thread
    start_flask()
