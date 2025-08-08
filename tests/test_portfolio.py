import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.portfolio import PortfolioService


class TestPortfolioService(unittest.TestCase):

    def _mock_db_conn(self):
        """Helper to create a standard mock for the database connection and cursor."""
        conn = MagicMock(name="Connection")
        cur = MagicMock(name="Cursor")
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.portfolio.get_db_connection')
    def test_sync_balances_success(self, mock_get_conn):
        """
        Verify that sync_balances correctly processes API data and updates the database.
        """
        # --- Arrange ---
        # Mock the database connection and cursor
        conn, cur = self._mock_db_conn()
        # Simulate resolving telegram_id to user_pk, then finding no portfolio, then getting new ID
        cur.fetchone.side_effect = [(1,), None, (100,)]
        # Simulate fetching one wallet for the user
        cur.fetchall.return_value = [('0xWalletAddress', 1)]  # address, chain_id
        mock_get_conn.return_value = conn

        # Mock the OKX Explorer API client
        explorer = MagicMock()
        explorer.get_all_balances.return_value = {
            'success': True,
            'data': [{
                "chainIndex": "1",
                "tokenAssets": [{
                    'symbol': 'ETH',
                    'balance': '1.5',
                    'tokenPrice': '3000.0',
                    'tokenContractAddress': '0xeeee'
                }]
            }]
        }
        service = PortfolioService(explorer=explorer)

        # --- Act ---
        result = service.sync_balances(telegram_id=12345)

        # --- Assert ---
        self.assertTrue(result)
        # Ensure the API was called with the correct wallet address and chain
        explorer.get_all_balances.assert_called_once_with('0xWalletAddress', chains=['1'])
        # Check that the holdings were deleted and then the new holding was inserted
        delete_call = any('DELETE FROM holdings' in str(call) for call in cur.execute.call_args_list)
        insert_call = any('INSERT INTO holdings' in str(call) for call in cur.execute.call_args_list)
        self.assertTrue(delete_call, "DELETE FROM holdings should have been called")
        self.assertTrue(insert_call, "INSERT INTO holdings should have been called")
        # Check that the transaction was committed
        conn.commit.assert_called_once()
        conn.close.assert_called_once()

    @patch('src.portfolio.get_db_connection')
    def test_get_snapshot_calculates_correctly(self, mock_get_conn):
        """
        Verify that get_snapshot correctly retrieves data and calculates portfolio value.
        """
        # --- Arrange ---
        conn, cur = self._mock_db_conn()
        # symbol, amount, decimals, value_usd
        mock_rows = [
            ('BTC', Decimal('50000000'), 8, Decimal('35000.0')),
            ('ETH', Decimal('2000000000000000000'), 18, Decimal('6000.0')),
        ]
        cur.fetchall.return_value = mock_rows
        mock_get_conn.return_value = conn

        service = PortfolioService(explorer=MagicMock())

        # --- Act ---
        snapshot = service.get_snapshot(telegram_id=12345)

        # --- Assert ---
        self.assertIn('total_value_usd', snapshot)
        self.assertIn('assets', snapshot)
        # Total value should be the sum of the 'value_usd' from the mock rows
        self.assertAlmostEqual(snapshot['total_value_usd'], 41000.0)
        self.assertEqual(len(snapshot['assets']), 2)
        # Check if the quantity for BTC was calculated correctly (0.5)
        self.assertAlmostEqual(snapshot['assets'][0]['quantity'], 0.5)
        # Check if the quantity for ETH was calculated correctly (2.0)
        self.assertAlmostEqual(snapshot['assets'][1]['quantity'], 2.0)
        conn.close.assert_called_once()

    @patch('src.portfolio.get_db_connection')
    @patch.object(PortfolioService, 'get_snapshot')
    def test_get_portfolio_performance(self, mock_get_snapshot, mock_get_conn):
        """Test the portfolio performance calculation."""
        # --- Arrange ---
        conn, cur = self._mock_db_conn()
        mock_get_conn.return_value = conn

        # Mock current and past portfolio values
        mock_get_snapshot.return_value = {"total_value_usd": 1100.0}
        cur.fetchone.return_value = (Decimal("1000.0"),)

        service = PortfolioService()

        # --- Act ---
        performance = service.get_portfolio_performance(user_id=12345, period_days=7)

        # --- Assert ---
        self.assertAlmostEqual(performance['current_value'], 1100.0)
        self.assertAlmostEqual(performance['past_value'], 1000.0)
        self.assertAlmostEqual(performance['absolute_change'], 100.0)
        self.assertAlmostEqual(performance['percentage_change'], 10.0)
        conn.close.assert_called_once()
