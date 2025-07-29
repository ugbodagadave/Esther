import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import warnings
from telegram.ext import ConversationHandler
from telegram.warnings import PTBUserWarning

# Suppress the specific PTBUserWarning at the module level, before it's triggered
warnings.filterwarnings("ignore", category=PTBUserWarning)

from src.main import start, help_command, handle_text, confirm_swap, cancel_swap, AWAIT_CONFIRMATION

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
    def test_handle_text_get_price_success(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "get_price",
            "entities": {"symbol": "ETH"}
        }
        # Mock OKX response
        mock_okx_client.get_live_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "3000000000"}
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "what is the price of eth"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        result = asyncio.run(handle_text(update, context))
        
        update.message.reply_text.assert_called_once_with("The current estimated price for ETH-USDT is $3000.00.")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.nlp_client')
    def test_handle_text_greeting(self, mock_nlp_client):
        mock_nlp_client.parse_intent.return_value = {"intent": "greeting", "entities": {}}

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "hello"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        result = asyncio.run(handle_text(update, context))
        
        update.message.reply_text.assert_called_once_with("Hello! How can I assist you with your trades today?")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.nlp_client')
    @patch('src.main.okx_client')
    def test_handle_text_buy_token_starts_conversation(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "buy_token",
            "entities": {"amount": "100", "symbol": "ETH", "currency": "USDC"}
        }
        # Mock OKX quote response
        mock_okx_client.get_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "33000000000000000"} # 0.033 ETH
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "buy 100 USDC worth of ETH"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        import asyncio
        result = asyncio.run(handle_text(update, context))

        # Check that the confirmation message is sent and we are in the right state
        self.assertIn("Please confirm the following swap:", update.message.reply_text.call_args[0][0])
        self.assertEqual(result, AWAIT_CONFIRMATION)
        self.assertIn('swap_details', context.user_data)

    @patch('src.main.okx_client')
    @patch.dict(os.environ, {"TEST_WALLET_ADDRESS": "test_wallet"})
    def test_confirm_swap_success(self, mock_okx_client):
        # Mock OKX response for the swap
        mock_okx_client.execute_swap.return_value = {
            "success": True,
            "data": {"toTokenAmount": "33000000000000000"} # 0.033 ETH
        }

        update = MagicMock()
        query = MagicMock()
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context = MagicMock()
        context.user_data = {
            'swap_details': {
                "from_token": "USDC",
                "to_token": "ETH",
                "from_token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "to_token_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "amount": "100",
                "amount_in_smallest_unit": "100000000",
                "source_chain_id": 1
            }
        }

        import asyncio
        with patch('src.main.DRY_RUN_MODE', True):
             result = asyncio.run(confirm_swap(update, context))

        # Check that the intermediate and final messages are sent
        self.assertEqual(query.edit_message_text.call_count, 2)
        query.edit_message_text.assert_any_call(text="Executing swap of 100 USDC for ETH...")
        
        # Get the keyword arguments of the second call
        final_call_kwargs = query.edit_message_text.call_args_list[1].kwargs
        self.assertIn("[DRY RUN] ✅ Swap Simulated Successfully!", final_call_kwargs.get('text'))
        self.assertEqual(result, ConversationHandler.END)
        self.assertNotIn('swap_details', context.user_data)

    def test_cancel_swap(self):
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        
        context = MagicMock()
        context.user_data = {'swap_details': {}}

        import asyncio
        result = asyncio.run(cancel_swap(update, context))

        update.callback_query.edit_message_text.assert_called_once_with(text="Swap cancelled.")
        self.assertEqual(result, ConversationHandler.END)
        self.assertNotIn('swap_details', context.user_data)

    @patch('src.main.nlp_client')
    @patch('src.main.okx_client')
    def test_handle_text_sell_token_starts_conversation(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "sell_token",
            "entities": {"amount": "0.5", "symbol": "ETH", "currency": "USDT"}
        }
        # Mock OKX quote response
        mock_okx_client.get_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "1800000000"} # 1800 USDT
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "sell 0.5 ETH for USDT"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        import asyncio
        result = asyncio.run(handle_text(update, context))

        # Check that the confirmation message is sent and we are in the right state
        self.assertIn("Please confirm the following swap:", update.message.reply_text.call_args[0][0])
        self.assertEqual(result, AWAIT_CONFIRMATION)
        self.assertIn('swap_details', context.user_data)

    @patch('src.main.nlp_client')
    def test_handle_text_set_stop_loss(self, mock_nlp_client):
        mock_nlp_client.parse_intent.return_value = {
            "intent": "set_stop_loss",
            "entities": {"symbol": "BTC", "price": "60000"}
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "set a stop-loss for BTC at 60000"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        result = asyncio.run(handle_text(update, context))
        
        update.message.reply_text.assert_called_once_with("I've set a stop-loss for BTC at $60000. I will notify you if the price drops to this level.")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.nlp_client')
    def test_handle_text_set_take_profit(self, mock_nlp_client):
        mock_nlp_client.parse_intent.return_value = {
            "intent": "set_take_profit",
            "entities": {"symbol": "ETH", "price": "3000"}
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "set a take-profit for ETH at 3000"
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        result = asyncio.run(handle_text(update, context))
        
        update.message.reply_text.assert_called_once_with("I've set a take-profit for ETH at $3000. I will notify you if the price rises to this level.")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.insights_client')
    def test_insights_command(self, mock_insights_client):
        """Test the /insights command."""
        mock_insights_client.generate_insights.return_value = "Here are your personalized insights."

        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        import asyncio
        from src.main import insights
        asyncio.run(insights(update, context))

        update.message.reply_text.assert_any_call("Generating your personalized market insights... This may take a moment.")
        update.message.reply_text.assert_any_call("Here are your personalized insights.")
        mock_insights_client.generate_insights.assert_called_once_with(123)

    @patch('src.main.nlp_client')
    @patch('src.main.okx_client')
    def test_handle_text_cross_chain_buy_token_starts_conversation(self, mock_okx_client, mock_nlp_client):
        # Mock NLP response
        mock_nlp_client.parse_intent.return_value = {
            "intent": "buy_token",
            "entities": {"amount": "100", "symbol": "ETH", "currency": "USDC", "source_chain": "Arbitrum", "destination_chain": "Polygon"}
        }
        # Mock OKX quote response
        mock_okx_client.get_live_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "33000000000000000"} # 0.033 ETH
        }

        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "buy 100 USDC worth of ETH on Polygon from Arbitrum"
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.user_data = {}

        import asyncio
        result = asyncio.run(handle_text(update, context))

        # Check that the confirmation message is sent and we are in the right state
        self.assertIn("Please confirm the following swap:", update.message.reply_text.call_args[0][0])
        self.assertEqual(result, AWAIT_CONFIRMATION)
        self.assertIn('swap_details', context.user_data)
        self.assertEqual(context.user_data['swap_details']['source_chain'], 'arbitrum')
        self.assertEqual(context.user_data['swap_details']['destination_chain'], 'polygon')
        mock_okx_client.get_live_quote.assert_called_once_with(
            from_token_address=unittest.mock.ANY,
            to_token_address=unittest.mock.ANY,
            amount=unittest.mock.ANY,
            chainId=42161
        )

    @patch('src.main.portfolio_service')
    def test_portfolio_command(self, mock_portfolio_service):
        mock_portfolio_service.sync_balances.return_value = True
        mock_portfolio_service.get_snapshot.return_value = {
            'total_value_usd': 100,
            'assets': [
                {'symbol': 'ETH', 'quantity': 1.0, 'value_usd': 100}
            ]
        }

        update = MagicMock()
        update.effective_user = MagicMock(id=123)
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        import asyncio
        from src.main import portfolio
        asyncio.run(portfolio(update, context))

        # Expect at least two reply_text calls (syncing + result)
        self.assertGreaterEqual(update.message.reply_text.call_count, 2)
        args_list = [call.args[0] for call in update.message.reply_text.call_args_list]
        self.assertTrue(any("Your Portfolio" in msg for msg in args_list))

if __name__ == '__main__':
    # Set dummy env var for NLPClient initialization during tests
    os.environ["GEMINI_API_KEY"] = "test_key"
    unittest.main()
