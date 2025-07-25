import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from src.main import start, help_command, handle_message
import os

class TestMainHandlers(unittest.TestCase):

    def test_start_command(self):
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        import asyncio
        asyncio.run(start(update, context))
        update.message.reply_text.assert_called_once_with("Hello! I am Esther, your AI-powered trading agent. How can I help you today?")

    def test_help_command(self):
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        import asyncio
        asyncio.run(help_command(update, context))
        update.message.reply_text.assert_called_once_with("I can help you with trading on OKX DEX. Try asking me for the price of a token, for example: 'What is the price of BTC?'")

    @patch('src.main.nlp_client')
    @patch('src.main.okx_client')
    def test_handle_message_get_price_success(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "get_price",
            "entities": {"symbol": "BTC"}
        }
        # Mock OKX response
        mock_okx_client.get_quote.return_value = {
            "symbol": "BTC-USDT",
            "price": "70000.0"
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "what is the price of btc"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(handle_message(update, context))
        
        mock_nlp_client.parse_intent.assert_called_once_with("what is the price of btc")
        mock_okx_client.get_quote.assert_called_once_with(from_token="BTC", to_token="USDT", amount="1")
        update.message.reply_text.assert_called_once_with("The current estimated price for BTC-USDT is $70000.0.")

    @patch('src.main.nlp_client')
    def test_handle_message_greeting(self, mock_nlp_client):
        mock_nlp_client.parse_intent.return_value = {"intent": "greeting", "entities": {}}

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "hello"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(handle_message(update, context))
        
        update.message.reply_text.assert_called_once_with("Hello! How can I assist you with your trades today?")

if __name__ == '__main__':
    # Set dummy env var for NLPClient initialization during tests
    os.environ["GEMINI_API_KEY"] = "test_key"
    unittest.main()
