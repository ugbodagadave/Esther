import unittest
from unittest.mock import MagicMock
from decimal import Decimal

from src.portfolio import PortfolioService

class TestPortfolioRebalance(unittest.TestCase):
    def test_suggest_rebalance_calculates_from_amount(self):
        # Arrange
        service = PortfolioService()
        
        # Mock the get_snapshot method to return a predictable portfolio
        service.get_snapshot = MagicMock(return_value={
            "total_value_usd": 1000.0,
            "assets": [
                {"symbol": "BTC", "quantity": 0.02, "value_usd": 800.0},
                {"symbol": "ETH", "quantity": 0.1, "value_usd": 200.0},
            ],
        })
        
        target_alloc = {"BTC": 50, "ETH": 50}

        # Act
        plan = service.suggest_rebalance(telegram_id=123, target_alloc=target_alloc)

        # Assert
        self.assertEqual(len(plan), 1)
        trade = plan[0]
        
        self.assertEqual(trade["from"], "BTC")
        self.assertEqual(trade["to"], "ETH")
        self.assertAlmostEqual(trade["usd_amount"], 300.0)
        
        # Expected from_amount = usd_amount / price
        # Price of BTC = 800.0 / 0.02 = 40000
        # Expected from_amount = 300.0 / 40000 = 0.0075
        self.assertAlmostEqual(trade["from_amount"], 0.0075)

if __name__ == "__main__":
    unittest.main()
