import unittest
from unittest.mock import AsyncMock, MagicMock
from src.main import start, help_command, echo

class TestMain(unittest.TestCase):

    def test_start_command(self):
        """Test the start command handler."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        import asyncio
        asyncio.run(start(update, context))
        
        update.message.reply_text.assert_called_once_with("Hello! I am Esther, your AI-powered trading agent. How can I help you today?")

    def test_help_command(self):
        """Test the help command handler."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        import asyncio
        asyncio.run(help_command(update, context))
        
        update.message.reply_text.assert_called_once_with("I can help you with trading on OKX DEX. Try asking me for the price of a token, for example: 'What is the price of BTC?'")

    def test_echo_handler(self):
        """Test the echo message handler."""
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "test message"
        update.message.reply_text = AsyncMock()
        
        context = MagicMock()
        
        import asyncio
        asyncio.run(echo(update, context))
        
        update.message.reply_text.assert_called_once_with("Echo: test message")

if __name__ == '__main__':
    unittest.main()
