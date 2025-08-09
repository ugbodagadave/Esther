import unittest
from unittest.mock import patch, MagicMock
from src.insights import InsightsClient
import os

class TestInsightsClient(unittest.TestCase):

    @patch('src.insights.PortfolioService')
    @patch('src.insights.OKXClient')
    @patch('google.generativeai.GenerativeModel')
    def test_generate_insights_success(self, mock_gen_model, mock_okx_client, mock_portfolio_svc):
        """Test generating insights successfully using real snapshot data path."""
        # Mock PortfolioService snapshot
        mock_port_instance = mock_portfolio_svc.return_value
        mock_port_instance.get_snapshot.return_value = {
            "total_value_usd": 1000.0,
            "assets": [
                {"symbol": "ETH", "quantity": 1.5, "value_usd": 3000.0},
                {"symbol": "USDC", "quantity": 1000.0, "value_usd": 1000.0},
            ],
        }

        # Mock OKX client
        mock_okx_instance = mock_okx_client.return_value
        mock_okx_instance.get_live_quote.side_effect = [
            {"success": True, "data": {"toTokenAmount": "3000000000"}},
            {"success": True, "data": {"toTokenAmount": "60000000000"}},
        ]

        # Mock Gemini model
        mock_pro_instance = mock_gen_model.return_value
        mock_pro_instance.generate_content.return_value = MagicMock(text="Your portfolio is looking good.")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            insights_client = InsightsClient()
            result = insights_client.generate_insights(123)

        self.assertEqual(result, "Your portfolio is looking good.")
        mock_pro_instance.generate_content.assert_called_once()
        mock_port_instance.get_snapshot.assert_called_once_with(123)

    @patch.dict(os.environ, clear=True)
    def test_init_no_api_key(self):
        """Test that InsightsClient raises an error if the API key is missing."""
        with self.assertRaises(ValueError):
            InsightsClient()

if __name__ == '__main__':
    unittest.main()
