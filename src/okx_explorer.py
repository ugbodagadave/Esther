import os
import time
import logging
import requests
import hmac
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.retry import compute_exponential_backoff_delays, sleep_with_backoff
from src.circuit import breaker, short_circuit_response

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
    """Simple typed wrapper around OKX Web3 DEX & Market endpoints.

    Covers read-only endpoints for balance and price lookups. This class
    abstracts the specific API paths and provides a consistent, simplified
    interface for the rest of the application.
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.base_url = os.getenv("OKX_BASE_URL", "https://web3.okx.com")
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
        headers = {
            "OK-ACCESS-KEY": self.api_key or "",
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.passphrase or "",
            "Content-Type": "application/json",
        }
        project = os.getenv("OKX_PROJECT_ID") or os.getenv("OK_ACCESS_PROJECT")
        if project:
            headers["OK-ACCESS-PROJECT"] = project
        return headers

    def _get(self, request_path: str, params: dict | None = None, endpoint_key: str | None = None) -> dict:
        """Generic GET with exponential backoff, circuit breaker, and unified response shape."""
        if endpoint_key and not breaker.allow_request(endpoint_key):
            return short_circuit_response(endpoint_key)

        query = "&".join([f"{k}={v}" for k, v in (params or {}).items()])
        full_path = f"{request_path}?{query}" if query else request_path
        url = f"{self.base_url}{full_path}"

        delays = compute_exponential_backoff_delays(self.max_retries)
        last_error = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.get(url, headers=self._headers("GET", full_path), timeout=10)
                resp.raise_for_status()
                payload = resp.json()
                if payload.get("code") == "0":
                    if endpoint_key:
                        breaker.record_success(endpoint_key)
                    return {"success": True, "data": payload.get("data", [])}
                error_msg = payload.get("msg", "Unknown API error")
                logger.error("OKX Explorer API error: %s", error_msg)
                last_error = error_msg
                if endpoint_key:
                    breaker.record_failure(endpoint_key)
            except requests.exceptions.HTTPError as e:
                logger.warning("HTTP error (%s) on attempt %d", e, attempt + 1)
                last_error = str(e)
                if endpoint_key:
                    breaker.record_failure(endpoint_key)
            except requests.exceptions.RequestException as e:
                logger.error("Network error while calling OKX Explorer: %s", e)
                last_error = str(e)
                if endpoint_key:
                    breaker.record_failure(endpoint_key)
                break
            sleep_with_backoff(attempt, delays)
        return {"success": False, "error": last_error or "Retries exhausted", "code": "E_OKX_HTTP"}

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def get_all_balances(self, address: str, chains: list[int] | None = None) -> dict:
        """Return a consolidated list of all native and token balances.

        This single endpoint provides balances and USD prices, so no separate
        price lookups are needed.

        Args:
            address: The wallet address to query.
            chains: A list of numeric chain IDs (e.g., [1, 56]). Defaults to
                    Ethereum mainnet.
        """
        if chains is None:
            chains = [1]

        chain_list = ",".join(map(str, chains))
        params = {"address": address, "chains": chain_list}
        return self._get(
            "/api/v5/dex/balance/all-token-balances-by-address",
            params,
            endpoint_key="dex/balance/all-token-balances-by-address",
        )

    def get_kline(self, symbol: str, bar: str = "1D", limit: int = 30) -> dict:
        """Return historical candle data.

        ``bar`` examples: 1m, 5m, 1H, 1D etc.
        ``limit`` max 100.
        """
        return self._get(
            "/api/v5/dex/market/candlesticks-history",
            {"instId": f"{symbol.upper()}-USDT", "bar": bar, "limit": limit},
            endpoint_key="dex/market/candlesticks-history",
        )


if __name__ == "__main__":
    explorer = OKXExplorer()
    addr = os.getenv("TEST_WALLET_ADDRESS", "0x000000000000000000000000000000000000dead")
    print("Checking all balances (dry run)...")
    print(explorer.get_all_balances(addr, chains=[1, 56])) # Check ETH and BSC 