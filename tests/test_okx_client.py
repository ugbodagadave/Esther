import unittest
from unittest.mock import patch, MagicMock
import requests
from src.okx_client import OKXClient

class TestOKXClient(unittest.TestCase):

    @patch('requests.get')
    def test_get_price_success(self, mock_get):
        """Test successful price fetching from OKX API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "msg": "",
            "data": [
                {
                    "instType": "SPOT",
                    "instId": "BTC-USDT",
                    "last": "65000.0",
                    "vol24h": "10000"
                }
            ]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_price("BTC-USDT")

        self.assertEqual(result['symbol'], "BTC-USDT")
        self.assertEqual(result['price'], "65000.0")
        self.assertNotIn('error', result)

    @patch('requests.get')
    def test_get_price_api_error(self, mock_get):
        """Test handling of an API error from OKX."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "51001",
            "msg": "Instrument ID does not exist",
            "data": []
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_price("INVALID-TOKEN")

        self.assertIn('error', result)
        self.assertEqual(result['error'], "Instrument ID does not exist")

    @patch('requests.get')
    def test_get_price_request_exception(self, mock_get):
        """Test handling of a requests exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        client = OKXClient()
        result = client.get_price("BTC-USDT")

        self.assertIn('error', result)
        self.assertEqual(result['error'], "Connection error")

if __name__ == '__main__':
    unittest.main()
