import unittest
from unittest.mock import patch, MagicMock
import requests
from src.okx_client import OKXClient

class TestOKXClient(unittest.TestCase):

    @patch('requests.get')
    def test_get_swap_quote_success(self, mock_get):
        """Test successful swap quote fetching."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "msg": "",
            "data": [
                {
                    "toTokenAmount": "10000",
                    "fromTokenAmount": "10",
                }
            ]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_swap_quote(
            from_token='ETH_ADDRESS', 
            to_token='USDT_ADDRESS', 
            amount='1000000'
        )

        self.assertEqual(result['toTokenAmount'], "10000")
        self.assertNotIn('error', result)

    @patch('requests.get')
    def test_get_swap_quote_api_error(self, mock_get):
        """Test handling of an API error from OKX."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "58100",
            "msg": "Invalid from-token address",
            "data": []
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_swap_quote(
            from_token='INVALID', 
            to_token='USDT_ADDRESS', 
            amount='1000000'
        )

        self.assertIn('error', result)
        self.assertEqual(result['error'], "Invalid from-token address")

    @patch('requests.get')
    def test_get_swap_quote_request_exception(self, mock_get):
        """Test handling of a requests exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        client = OKXClient()
        result = client.get_swap_quote(
            from_token='ETH_ADDRESS', 
            to_token='USDT_ADDRESS', 
            amount='1000000'
        )

        self.assertIn('error', result)
        self.assertEqual(result['error'], "Connection failed")

if __name__ == '__main__':
    unittest.main()
