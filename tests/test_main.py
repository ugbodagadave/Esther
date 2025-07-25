import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from src.main import start, help_command, handle_message
import os

class TestMainHandlers(unittest.TestCase):

    @patch('src.main.get_db_connection')
    def test_start_command_new_user(self, mock_get_conn):
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        # Mock fetchone to return None, simulating a new user
        mock_cursor.fetchone.return_value = None

        # Mock Telegram's user object
        update = MagicMock()
        update.effective_user = MagicMock(id=123, username='testuser')
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(start(update, context))

        # Verify user was created and correct message was sent
        mock_cursor.execute.assert_any_call("SELECT id FROM users WHERE telegram_id = %s;", (123,))
        mock_cursor.execute.assert_any_call("INSERT INTO users (telegram_id, username) VALUES (%s, %s);", (123, 'testuser'))
        update.message.reply_text.assert_called_once_with("Welcome! I've created an account for you. How can I help you get started with trading on OKX DEX?")

    @patch('src.main.get_db_connection')
    def test_start_command_existing_user(self, mock_get_conn):
        # Mock database to return an existing user
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,) # Simulate finding a user

        update = MagicMock()
        update.effective_user = MagicMock(id=123, username='testuser')
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(start(update, context))

        # Verify the welcome back message was sent
        update.message.reply_text.assert_called_once_with("Welcome back! How can I help you today?")

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
            "entities": {"symbol": "ETH"} # Using ETH as it's in our hardcoded map
        }
        # Mock OKX response
        mock_okx_client.get_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "3000000000"} # 3000 USDT (6 decimals)
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "what is the price of eth"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(handle_message(update, context))
        
        update.message.reply_text.assert_called_once_with("The current estimated price for ETH-USDT is $3000.00.")

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

    @patch('src.main.nlp_client')
    @patch('src.main.okx_client')
    def test_handle_message_buy_token(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "buy_token",
            "entities": {"amount": "100", "symbol": "ETH", "currency": "USDC"}
        }
        # Mock OKX response
        mock_okx_client.get_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "33000000000000000"} # 0.033 ETH
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "buy 100 USDC worth of ETH"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        asyncio.run(handle_message(update, context))

        # Check that the confirmation message is sent correctly
        self.assertIn("Quote: To buy 0.033000 ETH, it will cost 100 USDC. Please confirm to proceed.", update.message.reply_text.call_args[0][0])

if __name__ == '__main__':
    # Set dummy env var for NLPClient initialization during tests
    os.environ["GEMINI_API_KEY"] = "test_key"
    unittest.main()
