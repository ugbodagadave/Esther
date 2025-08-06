import threading
import os
from src.main import application
from gunicorn.app.base import BaseApplication

def start_bot():
    """Starts the Telegram bot with polling."""
    application.run_polling()

class StandaloneApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    # Start the Flask app with Gunicorn and Uvicorn workers
    from src.main import app
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 4,
        'worker_class': 'uvicorn.workers.UvicornWorker',
    }
    StandaloneApplication(app, options).run()
