import unittest
from unittest.mock import patch, MagicMock
import os
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