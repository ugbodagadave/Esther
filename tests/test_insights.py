import unittest
from unittest.mock import patch, MagicMock
from src.insights import InsightsClient
import os

class TestInsightsClient(unittest.TestCase):

    @patch('src.insights.get_db_connection')
    @patch('src.insights.OKXClient')
    @patch('google.generativeai.GenerativeModel')
    def test_generate_insights_success(self, mock_gen_model, mock_okx_client, mock_get_conn):
        """Test generating insights successfully."""
        # Mock database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.fetchall.return_value = [('My First Wallet',)]

        # Mock OKX client
        mock_okx_instance = mock_okx_client.return_value
        mock_okx_instance.get_live_quote.side_effect = [
            {"success": True, "data": {"toTokenAmount": "3000000000"}},
            {"success": True, "data": {"toTokenAmount": "60000000000"}}
        ]

        # Mock Gemini model
        mock_pro_instance = mock_gen_model.return_value
        mock_pro_instance.generate_content.return_value = MagicMock(text="Your portfolio is looking good.")

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
            insights_client = InsightsClient()
            result = insights_client.generate_insights(123)

        self.assertEqual(result, "Your portfolio is looking good.")
        mock_pro_instance.generate_content.assert_called_once()

    @patch.dict(os.environ, clear=True)
    def test_init_no_api_key(self):
        """Test that InsightsClient raises an error if the API key is missing."""
        with self.assertRaises(ValueError):
            InsightsClient()

if __name__ == '__main__':
    unittest.main()
