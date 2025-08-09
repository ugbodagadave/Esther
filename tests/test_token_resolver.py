import unittest
from unittest.mock import patch, MagicMock
from src.token_resolver import TokenResolver

class TestTokenResolver(unittest.TestCase):

    @patch('src.token_resolver.get_db_connection')
    def test_get_token_info_success(self, mock_get_conn):
        """Test successful resolution of token info."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = ('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 18)
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        resolver = TokenResolver()
        result = resolver.get_token_info('ETH')

        self.assertIsNotNone(result)
        self.assertEqual(result['address'], '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        self.assertEqual(result['decimals'], 18)

    @patch('src.token_resolver.get_db_connection')
    def test_get_token_info_not_found(self, mock_get_conn):
        """Test token info not found."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        resolver = TokenResolver()
        result = resolver.get_token_info('UNKNOWN')

        self.assertIsNone(result)

    @patch('src.token_resolver.get_db_connection')
    def test_btc_aliases_to_wbtc(self, mock_get_conn):
        """BTC should resolve to WBTC address/decimals for EVM contexts."""
        conn = MagicMock()
        cur = MagicMock()
        # Simulate DB miss so fallback to constants is exercised
        cur.fetchone.return_value = None
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        resolver = TokenResolver()
        result = resolver.get_token_info('BTC')

        # Expect WBTC details from constants
        self.assertIsNotNone(result)
        self.assertTrue(result['address'].lower().startswith('0x'))
        self.assertIn(result['decimals'], (8, 18))

    @patch('src.token_resolver.get_db_connection')
    def test_fallback_to_constants_when_db_miss(self, mock_get_conn):
        """If DB has no row, resolver should return constants when available."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        resolver = TokenResolver()
        result = resolver.get_token_info('USDC')

        self.assertIsNotNone(result)
        self.assertEqual(result['decimals'], 6)

if __name__ == '__main__':
    unittest.main()
