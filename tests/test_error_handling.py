import unittest
from unittest.mock import patch, AsyncMock
import psycopg2
from src.main import received_private_key
from src.exceptions import WalletAlreadyExistsError, InvalidWalletAddressError, DatabaseConnectionError

class TestErrorHandling(unittest.TestCase):

    @patch('src.main.add_wallet')
    @patch('src.main.encrypt_data')
    def test_received_private_key_success(self, mock_encrypt_data, mock_add_wallet):
        """Test the successful addition of a wallet."""
        update = AsyncMock()
        context = AsyncMock()
        
        update.effective_user.id = 123
        context.user_data = {'wallet_name': 'Test Wallet', 'wallet_address': '0x123'}
        update.message.web_app_data.data = 'test_private_key'
        mock_encrypt_data.return_value = 'encrypted_key'

        import asyncio
        asyncio.run(received_private_key(update, context))

        mock_add_wallet.assert_called_once_with(123, 'Test Wallet', '0x123', 'encrypted_key', chain_id=1)
        update.message.reply_text.assert_called_with("✅ Wallet 'Test Wallet' added successfully!")

    @patch('src.main.add_wallet')
    def test_received_private_key_wallet_exists(self, mock_add_wallet):
        """Test the case where the wallet already exists."""
        update = AsyncMock()
        context = AsyncMock()
        
        update.effective_user.id = 123
        context.user_data = {'wallet_name': 'Test Wallet', 'wallet_address': '0x123'}
        update.message.web_app_data.data = 'test_private_key'
        mock_add_wallet.side_effect = WalletAlreadyExistsError

        import asyncio
        asyncio.run(received_private_key(update, context))

        update.message.reply_text.assert_called_with("This wallet address has already been added to your profile.")

    def test_received_private_key_invalid_address(self):
        """Test the case where an invalid wallet address is provided."""
        update = AsyncMock()
        context = AsyncMock()
        
        update.effective_user.id = 123
        context.user_data = {'wallet_name': 'Test Wallet', 'wallet_address': 'invalid_address'}
        update.message.web_app_data.data = 'test_private_key'

        import asyncio
        asyncio.run(received_private_key(update, context))

        update.message.reply_text.assert_called_with("Invalid wallet address format.")

    @patch('src.main.add_wallet')
    def test_received_private_key_db_connection_error(self, mock_add_wallet):
        """Test the case where there is a database connection error."""
        update = AsyncMock()
        context = AsyncMock()
        
        update.effective_user.id = 123
        context.user_data = {'wallet_name': 'Test Wallet', 'wallet_address': '0x123'}
        update.message.web_app_data.data = 'test_private_key'
        mock_add_wallet.side_effect = DatabaseConnectionError

        import asyncio
        asyncio.run(received_private_key(update, context))

        update.message.reply_text.assert_called_with("I'm having trouble connecting to the database. Please try again later.")

if __name__ == '__main__':
    unittest.main()
