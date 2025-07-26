import unittest
from unittest.mock import patch, MagicMock
import os
from src.okx_client import OKXClient

class TestOKXClient(unittest.TestCase):

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('requests.get')
    def test_get_live_quote_success(self, mock_get):
        """Test successful fetching of a live swap quote."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{"toTokenAmount": "3000000000"}]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_live_quote("from_addr", "to_addr", "100")

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['toTokenAmount'], "3000000000")

    @patch.object(OKXClient, 'get_live_quote')
    def test_execute_swap_dry_run_success(self, mock_get_live_quote):
        """Test a successful dry run swap."""
        mock_get_live_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "500"}
        }
        
        client = OKXClient()
        result = client.execute_swap("from", "to", "100", "wallet_addr", dry_run=True)

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'simulated')
        self.assertEqual(result['data']['toTokenAmount'], '500')
        mock_get_live_quote.assert_called_once_with("from", "to", "100")

    @patch.object(OKXClient, 'get_live_quote')
    def test_execute_swap_dry_run_quote_fails(self, mock_get_live_quote):
        """Test a dry run swap where the initial quote fails."""
        mock_get_live_quote.return_value = {
            "success": False,
            "error": "Insufficient liquidity"
        }

        client = OKXClient()
        result = client.execute_swap("from", "to", "100", "wallet_addr", dry_run=True)

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Insufficient liquidity")

    @patch('requests.post')
    def test_execute_swap_real_run_success(self, mock_post):
        """Test a successful real swap execution."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{"txHash": "0x12345"}]
        }
        mock_post.return_value = mock_response

        client = OKXClient()
        result = client.execute_swap("from", "to", "100", "wallet_addr", dry_run=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['txHash'], "0x12345")

if __name__ == '__main__':
    unittest.main()
