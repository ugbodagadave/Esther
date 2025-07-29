import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.portfolio import PortfolioService

class TestPortfolioAnalytics(unittest.TestCase):

    @patch('src.portfolio.get_db_connection')
    def test_diversification(self, mock_get_conn):
        rows = [
            ('ETH', Decimal('1000000000000000000'), 18, Decimal('2000')),
            ('USDC', Decimal('1000000'), 6, Decimal('100')),
        ]
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = rows
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        svc = PortfolioService(explorer=MagicMock())
        alloc = svc.get_diversification(telegram_id=1)
        # ETH should be ~95.24%, USDC ~4.76% (2000 vs 100)
        self.assertAlmostEqual(alloc['ETH'], 95.24, places=1)
        self.assertAlmostEqual(alloc['USDC'], 4.76, places=1)

    @patch('src.portfolio.get_db_connection')
    def test_roi(self, mock_get_conn):
        rows = [
            ('ETH', Decimal('1000000000000000000'), 18, Decimal('2000')),
        ]
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = rows
        conn.cursor.return_value.__enter__.return_value = cur
        mock_get_conn.return_value = conn

        explorer = MagicMock()
        explorer.get_kline.return_value = {
            'success': True,
            'data': [
                {'open': '1500'},  # earliest price 30d ago
                {'open': '1600'},
            ]
        }
        svc = PortfolioService(explorer=explorer)
        roi = svc.get_roi(telegram_id=1, window_days=30)
        # (2000-1500)/1500 = 0.3333
        self.assertAlmostEqual(roi, 0.3333, places=4) 