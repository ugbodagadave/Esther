import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from src.monitoring import sync_all_portfolios, check_alerts

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

    @patch('src.monitoring.bot', new_callable=AsyncMock)
    @patch('src.monitoring.okx_client')
    @patch('src.monitoring.get_db_connection')
    async def test_check_alerts_trigger(self, mock_get_conn, mock_okx_client, mock_bot):
        """Test that an alert is triggered and the user is notified."""
        # Mock DB to return one active alert
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [(1, 123, 'ETH', 2000.0, 'below')]
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        # Mock OKX client to return a price that triggers the alert
        mock_okx_client.get_live_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "1900000000"} # 1900 USDT
        }

        await check_alerts()

        # Verify that the bot sent a message
        mock_bot.send_message.assert_awaited_once()
        # Verify that the alert was deactivated
        cur.execute.assert_any_call("UPDATE alerts SET is_active = FALSE WHERE id = %s;", (1,))
        conn.commit.assert_called_once()
