import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from telegram import Update, User
from telegram.ext import ConversationHandler, Application, ContextTypes

from src.database import initialize_database
from src.main import (
    start,
    help_command,
    handle_text,
    list_wallets,
    confirm_swap,
    received_wallet_address,
    received_private_key,
    _parse_period_to_days,
    portfolio_performance,
    get_price_chart_intent,
    set_default_wallet_start,
    set_default_wallet_callback,
    enable_live_trading_start,
    enable_live_trading_callback,
    AWAIT_WALLET_SELECTION,
    AWAIT_LIVE_TRADING_CONFIRMATION,
)

class TestPeriodParsing(unittest.TestCase):
    def test_parse_period_to_days(self):
        """Test the _parse_period_to_days helper function with various inputs."""
        test_cases = {
            "7d": 7,
            "14 days": 14,
            "28d": 28,
            "30 days": 30,
            "last month": 30,
            "1 month": 30,
            "last year": 365,
            "1 year": 365,
            "1y": 365,
            "90d": 90,
            "1": 1,
            "invalid": 7,  # Default
            None: 7,       # Default
            "": 7,         # Default
        }

        for period_str, expected_days in test_cases.items():
            with self.subTest(period_str=period_str):
                self.assertEqual(_parse_period_to_days(period_str), expected_days)

class TestMainHandlers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a basic test environment."""
        self.app = Application.builder().token("test-token").build()

    async def _create_update_context(self, text: str = "") -> tuple[Update, ContextTypes.DEFAULT_TYPE]:
        """Helper to create mock Update and Context objects."""
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        
        # Create a mock that has the same structure as the real Update object
        update = MagicMock(spec=Update)
        update.update_id = 12345
        
        # Mock the nested message object and its methods correctly
        update.message = MagicMock(spec=Update.message)
        update.message.text = text
        update.message.from_user = user
        update.message.reply_text = AsyncMock() # This is the key fix
        
        update.effective_user = user
        
        context = ContextTypes.DEFAULT_TYPE(application=self.app, chat_id=123, user_id=123)
        return update, context

    def _mock_db(self):
        """Helper to mock the database connection and cursor."""
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.main.get_db_connection')
    async def test_start_new_user(self, mock_get_conn):
        """Test the /start command for a new user."""
        update, context = await self._create_update_context()
        
        # Simulate a new user (fetchone returns None)
        mock_conn, mock_cur = self._mock_db()
        mock_cur.fetchone.return_value = None
        mock_get_conn.return_value = mock_conn

        await start(update, context)

        # Assertions
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        self.assertIn("Hello! I'm Esther", call_args.args[0])
        self.assertIsNotNone(call_args.kwargs.get('reply_markup'))

    @patch('src.main.get_db_connection')
    async def test_start_existing_user(self, mock_get_conn):
        """Test the /start command for an existing user."""
        update, context = await self._create_update_context()
        
        # Simulate an existing user
        mock_conn, mock_cur = self._mock_db()
        mock_cur.fetchone.return_value = (1,)  # User ID
        mock_get_conn.return_value = mock_conn

        await start(update, context)

        # Assertions
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        self.assertIn("Welcome back!", call_args.args[0])
        self.assertIsNotNone(call_args.kwargs.get('reply_markup'))

    async def test_help_command_as_text(self):
        """Test the /help command's text response."""
        update, context = await self._create_update_context()
        update.callback_query = None # Ensure this mock represents a text command
        await help_command(update, context)
        update.message.reply_text.assert_called_once()
        self.assertIn("Here's what I can do for you", update.message.reply_text.call_args.args[0])

    async def test_help_command_as_callback(self):
        """Test the /help command when triggered by a button."""
        update, context = await self._create_update_context()
        
        # Mock a callback query correctly with async methods
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        await help_command(update, context)
        
        query.answer.assert_called_once()
        query.edit_message_text.assert_called_once()
        self.assertIn("Here's what I can do for you", query.edit_message_text.call_args.args[0])

    @patch('src.main.list_wallets')
    @patch('src.main.nlp_client')
    async def test_handle_text_list_wallets(self, mock_nlp_client, mock_list_wallets):
        """Test that 'list_wallets' intent calls the correct handler."""
        # Arrange
        update, context = await self._create_update_context("show me my wallets")
        mock_nlp_client.parse_intent.return_value = {"intent": "list_wallets", "entities": {}}
        mock_list_wallets.return_value = None # It's an async function

        # Act
        result = await handle_text(update, context)

        # Assert
        mock_nlp_client.parse_intent.assert_called_once_with("show me my wallets", model_type='flash')
        mock_list_wallets.assert_called_once_with(update, context)
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.add_wallet_start')
    @patch('src.main.nlp_client')
    async def test_handle_text_add_wallet(self, mock_nlp_client, mock_add_wallet_start):
        """Test that 'add_wallet' intent calls the correct handler."""
        # Arrange
        update, context = await self._create_update_context("add a new wallet")
        mock_nlp_client.parse_intent.return_value = {"intent": "add_wallet", "entities": {}}
        mock_add_wallet_start.return_value = ConversationHandler.END # Simulate conversation end

        # Act
        result = await handle_text(update, context)

        # Assert
        mock_nlp_client.parse_intent.assert_called_once_with("add a new wallet", model_type='flash')
        mock_add_wallet_start.assert_called_once_with(update, context)
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.portfolio')
    @patch('src.main.nlp_client')
    async def test_handle_text_show_portfolio(self, mock_nlp_client, mock_portfolio):
        """Test that 'show_portfolio' intent calls the correct handler."""
        # Arrange
        update, context = await self._create_update_context("show my assets")
        mock_nlp_client.parse_intent.return_value = {"intent": "show_portfolio", "entities": {}}
        mock_portfolio.return_value = None # It's an async function

        # Act
        result = await handle_text(update, context)

        # Assert
        mock_nlp_client.parse_intent.assert_called_once_with("show my assets", model_type='flash')
        mock_portfolio.assert_called_once_with(update, context)
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.insights')
    @patch('src.main.nlp_client')
    async def test_handle_text_get_insights(self, mock_nlp_client, mock_insights):
        """Test that 'get_insights' intent calls the correct handler and uses the Pro model."""
        # Arrange
        update, context = await self._create_update_context("give me insights")
        # Simulate the two-step parsing process
        mock_nlp_client.parse_intent.side_effect = [
            {"intent": "get_insights", "entities": {}}, # First call (Flash)
            {"intent": "get_insights", "entities": {}}  # Second call (Pro)
        ]
        mock_insights.return_value = None

        # Act
        result = await handle_text(update, context)

        # Assert
        self.assertEqual(mock_nlp_client.parse_intent.call_count, 2)
        # Check that the second call specifically used the 'pro' model
        self.assertEqual(mock_nlp_client.parse_intent.call_args_list[1].kwargs['model_type'], 'pro')
        mock_insights.assert_called_once_with(update, context)
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.set_default_wallet_start')
    @patch('src.main.nlp_client')
    async def test_handle_text_set_default_wallet(self, mock_nlp_client, mock_set_default_wallet_start):
        """Test that 'set_default_wallet' intent calls the correct handler."""
        # Arrange
        update, context = await self._create_update_context("set my default wallet")
        mock_nlp_client.parse_intent.return_value = {"intent": "set_default_wallet", "entities": {}}
        mock_set_default_wallet_start.return_value = AWAIT_WALLET_SELECTION

        # Act
        result = await handle_text(update, context)

        # Assert
        mock_nlp_client.parse_intent.assert_called_once_with("set my default wallet", model_type='flash')
        mock_set_default_wallet_start.assert_called_once_with(update, context)
        self.assertEqual(result, AWAIT_WALLET_SELECTION)

    @patch('src.main.enable_live_trading_start')
    @patch('src.main.nlp_client')
    async def test_handle_text_enable_live_trading(self, mock_nlp_client, mock_enable_live_trading_start):
        """Test that 'enable_live_trading' intent calls the correct handler."""
        # Arrange
        update, context = await self._create_update_context("enable live trading")
        mock_nlp_client.parse_intent.return_value = {"intent": "enable_live_trading", "entities": {}}
        mock_enable_live_trading_start.return_value = AWAIT_LIVE_TRADING_CONFIRMATION

        # Act
        result = await handle_text(update, context)

        # Assert
        mock_nlp_client.parse_intent.assert_called_once_with("enable live trading", model_type='flash')
        mock_enable_live_trading_start.assert_called_once_with(update, context)
        self.assertEqual(result, AWAIT_LIVE_TRADING_CONFIRMATION)

    @patch('src.main.WEBHOOK_URL', "https://test.com")
    async def test_received_wallet_address_sends_web_app(self):
        """Test that received_wallet_address sends a web app button."""
        # Arrange
        update, context = await self._create_update_context("0x123")
        
        # Act
        result = await received_wallet_address(update, context)

        # Assert
        update.message.reply_text.assert_called_once()
        _, kwargs = update.message.reply_text.call_args
        self.assertIn("web_app", kwargs['reply_markup'].inline_keyboard[0][0].to_dict())
        self.assertEqual(result, 9) # AWAIT_WEB_APP_DATA

    @patch('src.database.get_db_connection')
    @patch('src.main.encrypt_data', return_value=b"encrypted_key")
    async def test_received_private_key_saves_wallet(self, mock_encrypt, mock_get_conn):
        """Test that received_private_key saves the wallet."""
        # Arrange
        update, context = await self._create_update_context()
        update.message.web_app_data = MagicMock()
        update.message.web_app_data.data = "test_private_key"
        
        context.user_data['wallet_name'] = "Test Wallet"
        context.user_data['wallet_address'] = "0x123"
        
        mock_conn, mock_cur = self._mock_db()
        mock_cur.fetchone.return_value = (1,) # User ID
        mock_get_conn.return_value = mock_conn

        # Act
        result = await received_private_key(update, context)

        # Assert
        mock_encrypt.assert_called_once_with("test_private_key")
        
        # Get the actual SQL query and arguments from the mock
        actual_call = mock_cur.execute.call_args
        self.assertIsNotNone(actual_call)
        
        # Clean up the SQL strings for comparison
        expected_sql = "INSERT INTO wallets (user_id, name, address, encrypted_private_key, chain_id) VALUES (%s, %s, %s, %s, %s);"
        actual_sql = ' '.join(actual_call.args[0].split())
        
        self.assertEqual(expected_sql, actual_sql)
        self.assertEqual(actual_call.args[1], (1, "Test Wallet", "0x123", b"encrypted_key", 1))
        
        update.message.reply_text.assert_called_once_with("✅ Wallet 'Test Wallet' added successfully!")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.generate_price_chart')
    @patch('src.main.okx_client.get_historical_price')
    async def test_get_price_chart_intent(self, mock_get_historical_price, mock_generate_price_chart):
        """Test the get_price_chart intent handler."""
        # Arrange
        update, context = await self._create_update_context("price chart for btc")
        entities = {"symbol": "BTC", "period": "7d"}

        mock_get_historical_price.return_value = {
            "success": True,
            "data": {"prices": [{"price": "60000", "time": "1672531200000"}]}
        }
        mock_generate_price_chart.return_value = b"fake_chart_image"
        update.message.reply_photo = AsyncMock()

        # Act
        await get_price_chart_intent(update, context, entities)

        # Assert
        mock_get_historical_price.assert_called_once()
        mock_generate_price_chart.assert_called_once()
        update.message.reply_photo.assert_called_once_with(
            photo=b"fake_chart_image",
            caption="Price chart for BTC (7d)"
        )

class TestLiveTradingSettings(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a basic test environment."""
        self.app = Application.builder().token("test-token").build()

    async def _create_update_context(self, text: str = "") -> tuple[Update, ContextTypes.DEFAULT_TYPE]:
        """Helper to create mock Update and Context objects."""
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        
        update = MagicMock(spec=Update)
        update.update_id = 12345
        
        update.message = MagicMock(spec=Update.message)
        update.message.text = text
        update.message.from_user = user
        update.message.reply_text = AsyncMock()
        
        update.effective_user = user
        
        context = ContextTypes.DEFAULT_TYPE(application=self.app, chat_id=123, user_id=123)
        return update, context

    def _mock_db(self):
        """Helper to mock the database connection and cursor."""
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.main.get_db_connection')
    async def test_set_default_wallet_start(self, mock_get_conn):
        """Test starting the set default wallet conversation."""
        update, context = await self._create_update_context()
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchone.return_value = (1,)  # User ID
        mock_cur.fetchall.return_value = [(1, "My Wallet", "0x123...abc")]

        result = await set_default_wallet_start(update, context)

        update.message.reply_text.assert_called_once()
        self.assertIn("Which wallet would you like to set as your default", update.message.reply_text.call_args.args[0])
        self.assertEqual(result, AWAIT_WALLET_SELECTION)

    @patch('src.main.get_db_connection')
    async def test_set_default_wallet_callback(self, mock_get_conn):
        """Test the callback for setting the default wallet."""
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "set_wallet_1"
        update.callback_query = query
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn

        result = await set_default_wallet_callback(update, context)

        mock_cur.execute.assert_called_once_with("UPDATE users SET default_wallet_id = %s WHERE telegram_id = %s;", (1, 123))
        query.edit_message_text.assert_called_once_with("✅ Default wallet has been set successfully.")
        self.assertEqual(result, ConversationHandler.END)

    @patch('src.main.get_db_connection')
    async def test_enable_live_trading_start(self, mock_get_conn):
        """Test starting the enable live trading conversation."""
        update, context = await self._create_update_context()
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        mock_cur.fetchone.return_value = (1, False) # default_wallet_id, live_trading_enabled

        result = await enable_live_trading_start(update, context)

        update.message.reply_text.assert_called_once()
        self.assertIn("Live trading is currently **disabled**", update.message.reply_text.call_args.args[0])
        self.assertEqual(result, AWAIT_LIVE_TRADING_CONFIRMATION)

    @patch('src.main.get_db_connection')
    async def test_enable_live_trading_callback(self, mock_get_conn):
        """Test the callback for enabling live trading."""
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        query.data = "enable_live_trading_yes"
        update.callback_query = query
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn

        result = await enable_live_trading_callback(update, context)

        mock_cur.execute.assert_called_once_with("UPDATE users SET live_trading_enabled = %s WHERE telegram_id = %s;", (True, 123))
        query.edit_message_text.assert_called_once_with("✅ Live trading has been **enabled**.", parse_mode='Markdown')
        self.assertEqual(result, ConversationHandler.END)

class TestConfirmSwap(unittest.IsolatedAsyncioTestCase):

    @patch('src.main.token_resolver', new_callable=MagicMock)
    @patch('src.main.get_db_connection')
    def setUp(self, mock_get_conn, mock_token_resolver):
        """Set up a basic test environment and initialize the database."""
        self.app = Application.builder().token("test-token").build()
        # Ensure the test database has the latest schema
        initialize_database()
        # Initialize the token resolver
        from src.token_resolver import TokenResolver
        global token_resolver
        token_resolver = TokenResolver()

    async def _create_update_context(self, text: str = "") -> tuple[Update, ContextTypes.DEFAULT_TYPE]:
        """Helper to create mock Update and Context objects."""
        user = User(id=123, first_name="Test", is_bot=False, username="testuser")
        
        update = MagicMock(spec=Update)
        update.update_id = 12345
        
        update.message = MagicMock(spec=Update.message)
        update.message.text = text
        update.message.from_user = user
        update.message.reply_text = AsyncMock()
        
        update.effective_user = user
        
        context = ContextTypes.DEFAULT_TYPE(application=self.app, chat_id=123, user_id=123)
        return update, context

    def _mock_db(self):
        """Helper to mock the database connection and cursor."""
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.main.token_resolver', new_callable=MagicMock)
    @patch('src.main.get_db_connection')
    @patch('src.main.okx_client.execute_swap')
    @patch('src.main.decrypt_data', return_value="decrypted_key")
    @patch('src.main.DRY_RUN_MODE', False)
    async def test_confirm_swap_live_trade(self, mock_decrypt, mock_execute_swap, mock_get_conn, mock_token_resolver):
        """Test confirm_swap executes a live trade when conditions are met."""
        # Arrange
        mock_token_resolver.get_token_info.return_value = {'decimals': 18}
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context.user_data['swap_details'] = {
            "from_token": "USDC", "to_token": "ETH", "from_token_address": "0x...", 
            "to_token_address": "0x...", "amount": "100", "amount_in_smallest_unit": "100000000",
            "source_chain_id": 1
        }
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        # Simulate live trading enabled and default wallet set
        mock_cur.fetchone.side_effect = [
            (True, 1), # user_settings
            ("0xLiveWallet", b"encrypted_key") # wallet_data
        ]
        
        mock_execute_swap.return_value = {"success": True, "data": {"toTokenAmount": "100000000000000000", "txHash": "0xabc"}}

        # Act
        await confirm_swap(update, context)

        # Assert
        mock_execute_swap.assert_called_once()
        _, kwargs = mock_execute_swap.call_args
        self.assertFalse(kwargs.get('dry_run'))
        self.assertEqual(kwargs.get('wallet_address'), "0xLiveWallet")
        self.assertEqual(kwargs.get('private_key'), "decrypted_key")
        query.edit_message_text.assert_called()
        # Check the final call to edit_message_text
        final_call = query.edit_message_text.call_args_list[-1]
        self.assertIn("LIVE", final_call.kwargs.get('text', ''))

    @patch('src.main.token_resolver', new_callable=MagicMock)
    @patch('src.main.get_db_connection')
    @patch('src.main.okx_client.execute_swap')
    @patch('src.main.DRY_RUN_MODE', False)
    async def test_confirm_swap_dry_run_when_live_disabled(self, mock_execute_swap, mock_get_conn, mock_token_resolver):
        """Test confirm_swap performs a dry run when live trading is disabled."""
        # Arrange
        mock_token_resolver.get_token_info.return_value = {'decimals': 18}
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context.user_data['swap_details'] = {
            "from_token": "USDC", "to_token": "ETH", "from_token_address": "0x...", 
            "to_token_address": "0x...", "amount": "100", "amount_in_smallest_unit": "100000000",
            "source_chain_id": 1
        }
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        # Simulate live trading disabled
        mock_cur.fetchone.return_value = (False, 1)
        
        mock_execute_swap.return_value = {"success": True, "data": {"toTokenAmount": "100000000000000000"}}

        # Act
        await confirm_swap(update, context)

        # Assert
        mock_execute_swap.assert_called_once()
        _, kwargs = mock_execute_swap.call_args
        self.assertTrue(kwargs.get('dry_run'))
        query.edit_message_text.assert_called()
        # Check the final call to edit_message_text
        final_call = query.edit_message_text.call_args_list[-1]
        self.assertIn("DRY RUN", final_call.kwargs.get('text', ''))

    @patch('src.main.token_resolver', new_callable=MagicMock)
    @patch('src.main.get_db_connection')
    @patch('src.main.okx_client.execute_swap')
    @patch('src.main.DRY_RUN_MODE', True)
    async def test_confirm_swap_respects_dry_run_mode(self, mock_execute_swap, mock_get_conn, mock_token_resolver):
        """Test that confirm_swap passes the DRY_RUN_MODE constant to execute_swap."""
        # Arrange
        mock_token_resolver.get_token_info.return_value = {'decimals': 18}
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context.user_data['swap_details'] = {
            "from_token": "USDC", "to_token": "ETH", "from_token_address": "0x...", 
            "to_token_address": "0x...", "amount": "100", "amount_in_smallest_unit": "100000000",
            "source_chain_id": 1
        }
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        # Simulate live trading enabled and default wallet set
        mock_cur.fetchone.side_effect = [
            (True, 1), # user_settings
        ]
        
        mock_execute_swap.return_value = {"success": True, "data": {"toTokenAmount": "100000000000000000"}}

        # Act
        await confirm_swap(update, context)

        # Assert
        mock_execute_swap.assert_called_once()
        _, kwargs = mock_execute_swap.call_args
        self.assertTrue(kwargs.get('dry_run'))
        final_call = query.edit_message_text.call_args_list[-1]
        self.assertIn("DRY RUN", final_call.kwargs.get('text', ''))

    @patch('src.main.get_db_connection')
    @patch('src.main.okx_client.execute_swap')
    async def test_confirm_swap_no_default_wallet(self, mock_execute_swap, mock_get_conn):
        """Test confirm_swap when live trading is enabled but no default wallet is set."""
        # Arrange
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context.user_data['swap_details'] = {
            "from_token": "USDC", "to_token": "ETH", "from_token_address": "0x...", 
            "to_token_address": "0x...", "amount": "100", "amount_in_smallest_unit": "100000000",
            "source_chain_id": 1
        }
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        # Simulate live trading enabled but no default wallet
        mock_cur.fetchone.return_value = (True, None)

        # Act
        await confirm_swap(update, context)

        # Assert
        mock_execute_swap.assert_not_called()
        query.edit_message_text.assert_called_once_with("Live trading is enabled, but you have not set a default wallet. Please use /setdefaultwallet.")

    @patch('src.main.get_db_connection')
    @patch('src.main.okx_client.execute_swap')
    async def test_confirm_swap_wallet_not_found(self, mock_execute_swap, mock_get_conn):
        """Test confirm_swap when the default wallet is not found in the database."""
        # Arrange
        update, context = await self._create_update_context()
        query = AsyncMock(spec=Update.callback_query)
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        update.callback_query = query
        
        context.user_data['swap_details'] = {
            "from_token": "USDC", "to_token": "ETH", "from_token_address": "0x...", 
            "to_token_address": "0x...", "amount": "100", "amount_in_smallest_unit": "100000000",
            "source_chain_id": 1
        }
        
        mock_conn, mock_cur = self._mock_db()
        mock_get_conn.return_value = mock_conn
        # Simulate live trading enabled, default wallet set, but wallet not found
        mock_cur.fetchone.side_effect = [
            (True, 1), # user_settings
            None # wallet_data
        ]

        # Act
        await confirm_swap(update, context)

        # Assert
        mock_execute_swap.assert_not_called()
        query.edit_message_text.assert_called_once_with("Your default wallet could not be found. Please set it again.")

if __name__ == '__main__':
    unittest.main()
