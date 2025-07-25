import os
import requests
import logging
import hmac
import base64
import time
import json
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_timestamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

def sign(message, secret_key):
    mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    return base64.b64encode(mac.digest()).decode()

class OKXClient:
    def __init__(self):
        self.base_url = "https://www.okx.com"
        self.api_key = os.getenv("OKX_API_KEY")
        self.api_secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_API_PASSPHRASE")

    def _get_request_headers(self, method, request_path, body=''):
        timestamp = get_timestamp()
        message = timestamp + method + request_path + body
        signature = sign(message, self.api_secret)
        
        return {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }

    def get_price(self, symbol: str) -> dict:
        """
        Fetches the current price of a trading pair from OKX.
        e.g. symbol='BTC-USDT'
        """
        try:
            url = f"{self.base_url}/api/v5/market/ticker?instId={symbol.upper()}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                ticker_data = data.get("data", [{}])[0]
                return {"symbol": symbol, "price": ticker_data.get("last")}
            else:
                logger.error(f"Error from OKX API: {data.get('msg')}")
                return {"error": data.get("msg")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from OKX: {e}")
            return {"error": str(e)}

    def get_account_balance(self):
        """
        Fetches the account balance to verify API credentials.
        """
        try:
            request_path = '/api/v5/account/balance'
            headers = self._get_request_headers('GET', request_path)
            url = f"{self.base_url}{request_path}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                return {"success": True, "data": data.get("data")}
            else:
                logger.error(f"Error from OKX API: {data.get('msg')}")
                return {"success": False, "error": data.get("msg")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching account balance: {e}")
            return {"success": False, "error": str(e)}

    def get_swap_quote(self, from_token: str, to_token: str, amount: str, chain_index: int = 1, slippage: float = 0.05) -> dict:
        """
        Fetches a swap quote from the OKX DEX aggregator.
        """
        # This method will be fully implemented later.
        logger.info("get_swap_quote is not yet implemented.")
        return {"error": "Not implemented"}

if __name__ == '__main__':
    # Example usage to test API credentials
    print("Attempting to verify OKX API credentials...")
    client = OKXClient()
    if not all([client.api_key, client.api_secret, client.passphrase]):
        print("OKX credentials not found in .env file.")
    else:
        balance_info = client.get_account_balance()
        if balance_info.get("success"):
            print("Successfully connected to OKX API and fetched balance.")
            # print("Balance Data:", balance_info.get("data")) # Optionally print for more detail
        else:
            print(f"Failed to connect to OKX API. Error: {balance_info.get('error')}")
