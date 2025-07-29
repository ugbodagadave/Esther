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
    def test_get_native_balance_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"code": "0", "data": [{"balance": "123"}]}
        mock_get.return_value = mock_resp

        result = self.explorer.get_native_balance("0xabc", chain_id=1)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], [{"balance": "123"}])

    @patch("src.okx_explorer.requests.get")
    def test_get_spot_price_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"code": "10002", "msg": "Invalid symbol"}
        mock_get.return_value = mock_resp

        result = self.explorer.get_spot_price("BAD")
        self.assertFalse(result["success"])
        self.assertIn("Invalid symbol", result["error"]) 