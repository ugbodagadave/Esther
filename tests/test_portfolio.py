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
        cur.fetchall.return_value = [('0xabc', 1)] # address, chain_id
        conn.cursor.return_value.__enter__.return_value = cur
        return conn, cur

    @patch('src.portfolio.get_db_connection')
    def test_sync_balances_basic(self, mock_get_conn):
        # Arrange DB mocks
        conn, cur = self._mock_db()
        mock_get_conn.return_value = conn

        # Arrange Explorer mocks
        explorer = MagicMock()
        explorer.get_all_balances.return_value = {
            'success': True,
            'data': [
                {
                    "chainIndex": "1",
                    "tokenAssets": [
                        {
                            'tokenContractAddress': '0xeeee',
                            'symbol': 'ETH',
                            'balance': '1.0',
                            'tokenPrice': '2000.0'
                        },
                        {
                            'tokenContractAddress': '0xa0b8',
                            'symbol': 'USDC',
                            'balance': '100.0',
                            'tokenPrice': '1.0'
                        }
                    ]
                }
            ]
        }

        svc = PortfolioService(explorer=explorer)

        # Act
        ok = svc.sync_balances(telegram_id=123)

        # Expect success path
        self.assertTrue(ok)
        # Holdings insertion should be called twice
        self.assertEqual(cur.execute.call_count, 8) # select user, select portfolio, insert portfolio, select wallets, delete holdings, insert holdings (x2), update portfolios
        executes = [c[0][0] for c in cur.execute.call_args_list]
        self.assertEqual(len([s for s in executes if 'INSERT INTO holdings' in s]), 2)

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