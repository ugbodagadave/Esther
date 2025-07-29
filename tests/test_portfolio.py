import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.portfolio import PortfolioService


class TestPortfolioService(unittest.TestCase):

    def _mock_db(self):
        """Return mocked connection + cursor matching sync_balances flow."""
        conn = MagicMock()
        cur = MagicMock()
        # fetchone is called 3 times in sync_balances
        cur.fetchone.side_effect = [
            (1,),   # user id
            None,   # portfolio id absent -> triggers insert
            (100,), # inserted portfolio id
        ]
        # fetchall returns same wallets list for any call
        cur.fetchall.return_value = [('0xabc',)]
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.portfolio.get_db_connection')
    def test_sync_balances_basic(self, mock_get_conn):
        # Arrange DB mocks
        conn, cur = self._mock_db()
        mock_get_conn.return_value = conn

        # Arrange Explorer mocks
        explorer = MagicMock()
        explorer.get_native_balance.return_value = {
            'success': True,
            'data': [{
                'symbol': 'ETH',
                'tokenAddress': '0xeeee',
                'balance': '1000000000000000000',  # 1 ETH
                'tokenDecimal': 18,
            }]
        }
        explorer.get_token_balances.return_value = {
            'success': True,
            'data': [{
                'tokenAddress': '0xa0b8',
                'symbol': 'USDC',
                'balance': '1000000',  # 1 USDC (6 decimals)
                'decimals': 6,
            }]
        }
        explorer.get_spot_price.return_value = {
            'success': True,
            'data': [{'last': '1'}]
        }

        svc = PortfolioService(explorer=explorer)

        # Act
        ok = svc.sync_balances(telegram_id=123)

        # Expect success path
        self.assertTrue(ok)
        # Holdings insertion should be called
        executes = [c[0][0] for c in cur.execute.call_args_list]
        assert any('INSERT INTO holdings' in sql for sql in executes)

    @patch('src.portfolio.get_db_connection')
    def test_get_snapshot(self, mock_get_conn):
        # Prepare mocked DB rows (symbol, amount, decimals, value_usd)
        rows = [
            ('ETH', Decimal('1000000000000000000'), 18, Decimal('2000')),
            ('USDC', Decimal('1000000'), 6, Decimal('1')),
        ]
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = rows
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        svc = PortfolioService(explorer=MagicMock())
        snap = svc.get_snapshot(telegram_id=123)

        self.assertAlmostEqual(snap['total_value_usd'], 2001.0, places=2)
        self.assertEqual(len(snap['assets']), 2) 