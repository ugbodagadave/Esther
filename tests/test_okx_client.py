import unittest
from unittest.mock import patch, MagicMock
import requests
import os
from src.okx_client import OKXClient

class TestOKXClient(unittest.TestCase):

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('requests.get')
    def test_verify_credentials_success(self, mock_get):
        """Test successful credential verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "0", "data": "Credentials are valid."}
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.verify_credentials()

        self.assertTrue(result['success'])
        self.assertEqual(result['data'], "Credentials are valid.")

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('requests.get')
    def test_verify_credentials_failure(self, mock_get):
        """Test failed credential verification due to API error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "50001", "msg": "Invalid API Key"}
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.verify_credentials()

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Invalid API Key")

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('requests.get')
    def test_get_quote_success(self, mock_get):
        """Test successful fetching of a swap quote."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{"toTokenAmount": "3000000000"}]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_quote("from_addr", "to_addr", "100")

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['toTokenAmount'], "3000000000")

if __name__ == '__main__':
    unittest.main()
