import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from src.okx_client import OKXClient
from src.constants import DRY_RUN_MODE

class TestOKXClient(unittest.TestCase):

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('src.okx_client.requests.get')
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
        mock_get_live_quote.assert_called_once_with("from", "to", "100", 1)

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

    @patch('src.okx_client.OKXClient.get_live_quote')
    @patch('src.okx_client.requests.post')
    def test_execute_swap_real_run_success(self, mock_post, mock_get_live_quote):
        """Test a successful real swap execution."""
        mock_get_live_quote.return_value = {"success": True, "data": {}}
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

    @patch('src.okx_client.requests.get', side_effect=requests.exceptions.HTTPError("500 Server Error"))
    @patch('time.sleep', return_value=None) # Mock time.sleep to avoid delays
    def test_get_live_quote_retry_logic(self, mock_sleep, mock_get):
        """Test the retry logic for get_live_quote."""
        client = OKXClient(max_retries=3, retry_delay=0.1)
        result = client.get_live_quote("from", "to", "100")

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Failed to fetch quote after multiple retries.")
        self.assertEqual(mock_get.call_count, 3)

    @patch('src.okx_client.OKXClient.get_live_quote')
    @patch('src.okx_client.requests.post', side_effect=requests.exceptions.HTTPError("500 Server Error"))
    @patch('time.sleep', return_value=None)
    def test_execute_swap_retry_logic(self, mock_sleep, mock_post, mock_get_live_quote):
        """Test the retry logic for execute_swap."""
        mock_get_live_quote.return_value = {"success": True, "data": {}}
        client = OKXClient(max_retries=3, retry_delay=0.1)
        result = client.execute_swap("from", "to", "100", "wallet_addr", dry_run=False)

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Failed to execute swap after multiple retries.")
        self.assertEqual(mock_post.call_count, 3)

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('src.okx_client.requests.get')
    def test_get_live_quote_with_chain_id(self, mock_get):
        """Test get_live_quote with a specific chainId."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{"toTokenAmount": "12345"}]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        client.get_live_quote("from_addr", "to_addr", "100", chainId=42)

        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertIn("chainId=42", called_url)

    @patch.object(OKXClient, 'get_live_quote')
    def test_execute_swap_with_chain_id(self, mock_get_live_quote):
        """Test execute_swap passes chainId to get_live_quote."""
        mock_get_live_quote.return_value = {
            "success": True,
            "data": {"toTokenAmount": "500"}
        }
        
        client = OKXClient()
        client.execute_swap("from", "to", "100", "wallet_addr", chainId=42, dry_run=True)

        mock_get_live_quote.assert_called_once_with("from", "to", "100", 42)

    @patch('src.okx_client.DRY_RUN_MODE', True)
    @patch.object(OKXClient, 'get_live_quote')
    def test_execute_swap_respects_dry_run_mode_constant_true(self, mock_get_live_quote):
        """Test that execute_swap defaults to DRY_RUN_MODE=True from constants."""
        mock_get_live_quote.return_value = {"success": True, "data": {}}
        
        client = OKXClient()
        # Call execute_swap without the dry_run parameter
        result = client.execute_swap("from", "to", "100", "wallet_addr")

        self.assertTrue(result['success'])
        self.assertEqual(result['status'], 'simulated')
        mock_get_live_quote.assert_called_once()

    @patch('src.okx_client.DRY_RUN_MODE', False)
    @patch('src.okx_client.OKXClient.get_live_quote')
    @patch('src.okx_client.requests.post')
    def test_execute_swap_respects_dry_run_mode_constant_false(self, mock_post, mock_get_live_quote):
        """Test that execute_swap defaults to DRY_RUN_MODE=False from constants."""
        mock_get_live_quote.return_value = {"success": True, "data": {}}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": "0", "data": [{"txHash": "0xreal"}]}
        mock_post.return_value = mock_response

        client = OKXClient()
        # Call execute_swap without the dry_run parameter
        result = client.execute_swap("from", "to", "100", "wallet_addr")

        self.assertTrue(result['success'])
        self.assertNotIn('status', result) # Real swaps don't have a 'status' field
        self.assertEqual(result['data']['txHash'], "0xreal")
        mock_post.assert_called_once()

    @patch.dict(os.environ, {
        "OKX_API_KEY": "test_key",
        "OKX_API_SECRET": "test_secret",
        "OKX_API_PASSPHRASE": "test_passphrase"
    })
    @patch('src.okx_client.requests.get')
    def test_get_historical_price_success(self, mock_get):
        """Test successful fetching of historical price data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "0",
            "data": [{"time": "1672531200000", "price": "16547.2"}]
        }
        mock_get.return_value = mock_response

        client = OKXClient()
        result = client.get_historical_price("token_addr", 1, "7d")

        self.assertTrue(result['success'])
        self.assertEqual(result['data']['price'], "16547.2")
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        self.assertIn("chainIndex=1", called_url)
        self.assertIn("period=1d", called_url)

if __name__ == '__main__':
    unittest.main()
