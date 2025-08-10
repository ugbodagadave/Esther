import unittest
from unittest.mock import patch, MagicMock
import os
import requests
from src.okx_explorer import OKXExplorer

class TestOKXExplorer(unittest.TestCase):

    def setUp(self):
        # Provide dummy env vars so headers generate deterministically
        patcher = patch.dict(os.environ, {
            "OKX_API_KEY": "dummy",
            "OKX_API_SECRET": "dummy",
            "OKX_API_PASSPHRASE": "dummy"
        })
        patcher.start()
        self.addCleanup(patcher.stop)
        self.explorer = OKXExplorer()

    @patch("src.okx_explorer.requests.get")
    def test_get_all_balances_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "code": "0",
            "data": [
                {
                    "chainIndex": "1",
                    "tokenAssets": [{"symbol": "ETH", "balance": "1.23", "tokenPrice": "3000"}]
                }
            ]
        }
        mock_get.return_value = mock_resp

        result = self.explorer.get_all_balances("0xabc", chains=[1])
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["tokenAssets"][0]["symbol"], "ETH")

    @patch("src.okx_explorer.requests.get")
    def test_get_kline_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"code": "51000", "msg": "Instrument not found"}
        mock_get.return_value = mock_resp

        result = self.explorer.get_kline("NONEXISTENT")
        self.assertFalse(result["success"])
        self.assertIn("Instrument not found", result["error"])

    def test_default_base_url(self):
        explorer = OKXExplorer()
        self.assertEqual(explorer.base_url, "https://web3.okx.com")

    @patch("src.circuit.breaker.allow_request", return_value=False)
    def test_breaker_short_circuit_balances(self, mock_allow):
        res = self.explorer.get_all_balances("0xabc", [1])
        self.assertFalse(res["success"])
        self.assertEqual(res.get("code"), "E_OKX_HTTP")
        self.assertIn("circuit", res)

    @patch("src.okx_explorer.requests.get")
    @patch("src.okx_explorer.sleep_with_backoff", return_value=None)
    def test_retry_helper_called(self, mock_sleep, mock_get):
        mock_get.side_effect = requests.exceptions.HTTPError("500")
        res = self.explorer.get_kline("BTC", bar="1D", limit=3)
        self.assertFalse(res["success"]) 
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 3) 