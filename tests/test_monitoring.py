import unittest
from unittest.mock import patch, MagicMock
import asyncio

from src.monitoring import sync_all_portfolios

class TestMonitoring(unittest.IsolatedAsyncioTestCase):

    @patch('src.monitoring.portfolio_service')
    @patch('src.monitoring.get_db_connection')
    async def test_sync_all_portfolios(self, mock_get_conn, mock_portfolio_service):
        # Mock DB to return two users
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [(1, 111), (2, 222)]
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        mock_portfolio_service.sync_balances.return_value = True

        await sync_all_portfolios()

        # Ensure sync_balances called for both users
        calls = [c.args[0] for c in mock_portfolio_service.sync_balances.call_args_list]
        self.assertListEqual(calls, [111, 222])
