import os
import time
import logging
import requests
import hmac
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables early so they are available for any import order
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def _timestamp() -> str:
    """Return RFC3339/ISO timestamp in milliseconds, matching OKX requirement."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _sign(message: str, secret_key: str) -> str:
    mac = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), digestmod="sha256")
    return base64.b64encode(mac.digest()).decode()


class OKXExplorer:
    """Simple typed wrapper around OKX Web3 Explorer endpoints.

    Only *read-only* endpoints are covered – no trading or swap execution here.
    All methods return a dict with keys: ``success`` (bool) and either ``data`` or ``error``.
    This mirrors the behaviour of :pyclass:`src.okx_client.OKXClient` for consistency.
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        # Explorer endpoints are served from the main okx.com host (not web3.okx.com)
        self.base_url = os.getenv("OKX_BASE_URL", "https://www.okx.com")
        self.api_key = os.getenv("OKX_API_KEY")
        self.api_secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_API_PASSPHRASE")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if not all([self.api_key, self.api_secret, self.passphrase]):
            logger.warning("OKX API credentials missing – signed requests may fail.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _headers(self, method: str, request_path: str, body: str = "") -> dict:
        ts = _timestamp()
        signature = _sign(ts + method + request_path + body, self.api_secret or "")
        return {
            "OK-ACCESS-KEY": self.api_key or "",
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.passphrase or "",
            "Content-Type": "application/json",
        }

    def _get(self, request_path: str, params: dict | None = None) -> dict:
        """Generic GET with retry and unified response shape."""
        query = "&".join([f"{k}={v}" for k, v in (params or {}).items()])
        full_path = f"{request_path}?{query}" if query else request_path
        url = f"{self.base_url}{full_path}"

        for attempt in range(self.max_retries):
            try:
                resp = requests.get(url, headers=self._headers("GET", full_path), timeout=10)
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("code") == "0":
                    return {"success": True, "data": payload.get("data", [])}
                error_msg = payload.get("msg", "Unknown API error")
                logger.error("OKX Explorer API error: %s", error_msg)
                return {"success": False, "error": error_msg}
            except requests.exceptions.HTTPError as e:
                logger.warning("HTTP error (%s) on attempt %d – retrying in %ss", e, attempt + 1, self.retry_delay)
                time.sleep(self.retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error("Network error while calling OKX Explorer: %s", e)
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Retries exhausted"}

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def _chain_param(self, chain: int | str) -> dict:
        """Translate *chain* into the expected query param accepted by OKX Explorer.

        The public docs are sparse, but empirically the explorer endpoints accept
        *either* ``chainShortName`` (ETH, BSC, etc.) **or** the numeric
        ``chainId``.  Supplying the wrong param leads to HTTP 404.

        To be future-proof we send *both* – servers ignore the unknown field.
        """
        mapping = {1: "ETH", 56: "BSC", 137: "POL", 43114: "AVAX"}
        if isinstance(chain, int):
            return {"chainId": chain, "chainShortName": mapping.get(chain, "")}
        # str path – assume caller already passed short name
        return {"chainShortName": chain}

    def get_native_balance(self, address: str, chain: int | str = 1) -> dict:
        """Return native coin balance (e.g. ETH or BNB).

        ``chain`` may be the numeric chainId (1 = Ethereum) or the
        ``chainShortName`` string used by OKX ("ETH", "BSC", …).
        """
        params = {"address": address} | self._chain_param(chain)
        return self._get("/api/v5/explorer/address/balance", params)

    def get_token_balances(self, address: str, chain: int | str = 1) -> dict:
        """Return list of ERC-20 (or chain equivalent) balances for *address*."""
        params = {"address": address} | self._chain_param(chain)
        return self._get("/api/v5/explorer/address/token_balance", params)

    def get_spot_price(self, symbol: str) -> dict:
        """Return latest spot price vs USDT."""
        return self._get(
            "/api/v5/explorer/market/token_ticker",
            {"symbol": f"{symbol.upper()}-USDT"},
        )

    def get_kline(self, symbol: str, bar: str = "1D", limit: int = 30) -> dict:
        """Return historical candle data.

        ``bar`` examples: 1m, 5m, 1H, 1D etc.
        ``limit`` max 100.
        """
        return self._get(
            "/api/v5/explorer/market/kline",
            {"symbol": f"{symbol.upper()}-USDT", "bar": bar, "limit": limit},
        )


if __name__ == "__main__":
    explorer = OKXExplorer()
    addr = os.getenv("TEST_WALLET_ADDRESS", "0x000000000000000000000000000000000000dead")
    print("Checking native balance (dry run)...")
    print(explorer.get_native_balance(addr)) 