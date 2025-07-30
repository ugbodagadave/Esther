import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from telegram import Update, User
from telegram.ext import ConversationHandler, Application, ContextTypes

from src.main import (
    start,
    help_command,
    handle_text,
    list_wallets,
    # Add other handlers you need to test
)

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
        mock_nlp_client.parse_intent.assert_called_once_with("show me my wallets")
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
        mock_nlp_client.parse_intent.assert_called_once_with("add a new wallet")
        mock_add_wallet_start.assert_called_once_with(update, context)
        self.assertEqual(result, ConversationHandler.END)

if __name__ == '__main__':
    unittest.main() 