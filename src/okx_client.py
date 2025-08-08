import os
import requests
import os
import requests
import logging
import hmac
import base64
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.constants import DRY_RUN_MODE

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
    def __init__(self, max_retries=3, retry_delay=2):
        self.base_url = "https://web3.okx.com"
        self.api_key = os.getenv("OKX_API_KEY")
        self.api_secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_API_PASSPHRASE")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

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

    def get_live_quote(self, from_token_address: str, to_token_address: str, amount: str, chainId: int = 1) -> dict:
        """
        Fetches a real swap quote from the OKX DEX aggregator with retry logic.
        """
        for attempt in range(self.max_retries):
            try:
                request_path = '/api/v5/dex/aggregator/quote'
                params = {
                    "chainId": chainId,
                    "amount": amount,
                    "toTokenAddress": to_token_address,
                    "fromTokenAddress": from_token_address
                }
                
                query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
                full_request_path = f"{request_path}?{query_string}"

                headers = self._get_request_headers('GET', full_request_path)
                url = f"{self.base_url}{full_request_path}"
                
                logger.info(f"Sending GET request to OKX: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == "0":
                    return {"success": True, "data": data.get("data", [{}])[0]}
                else:
                    error_msg = data.get("msg", "Unknown API error")
                    logger.error(f"Error fetching quote from OKX API: {error_msg}")
                    return {"success": False, "error": f"API Error: {error_msg}"}
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP Error on attempt {attempt + 1}: {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching quote: {e}")
                return {"success": False, "error": f"A network error occurred: {e}"}
        
        return {"success": False, "error": "Failed to fetch quote after multiple retries."}

    def execute_swap(self, from_token_address: str, to_token_address: str, amount: str, wallet_address: str, chainId: int = 1, slippage: str = "1", dry_run: bool = None) -> dict:
        """
        Executes a swap. It always fetches a quote first.
        If dry_run is True, it only simulates the transaction.
        If dry_run is False, it executes a real swap on the blockchain.
        """
        if dry_run is None:
            dry_run = DRY_RUN_MODE
        # Always get a quote first
        quote_response = self.get_live_quote(from_token_address, to_token_address, amount, chainId)

        if not quote_response.get("success"):
            return quote_response  # Propagate the error from get_live_quote

        if dry_run:
            logger.info(f"Executing DRY RUN swap from {from_token_address} to {to_token_address}")
            return {
                "success": True,
                "status": "simulated",
                "data": quote_response["data"],
                "message": "✅ Swap simulated successfully (no real transaction)"
            }
        
        # Proceed with the real swap if not a dry run
        logger.info(f"Executing REAL swap for wallet {wallet_address}")
        for attempt in range(self.max_retries):
            try:
                request_path = '/api/v5/dex/aggregator/swap'
                body = {
                    "fromTokenAddress": from_token_address,
                    "toTokenAddress": to_token_address,
                    "amount": amount,
                    "walletAddress": wallet_address,
                    "slippage": slippage,
                    "chainId": chainId
                }
                
                body_str = json.dumps(body)
                headers = self._get_request_headers('POST', request_path, body_str)
                url = f"{self.base_url}{request_path}"
                
                logger.info(f"Sending POST request to OKX: {url}")
                response = requests.post(url, headers=headers, json=body, timeout=15)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == "0":
                    logger.info(f"Successfully executed swap: {data.get('msg')}")
                    return {"success": True, "data": data.get("data", [{}])[0]}
                else:
                    error_msg = data.get("msg", "Unknown API error")
                    logger.error(f"Error executing swap on OKX API: {error_msg}")
                    return {"success": False, "error": f"API Error: {error_msg}"}
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP Error on attempt {attempt + 1}: {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error executing swap: {e}")
                return {"success": False, "error": f"A network error occurred: {e}"}
        
        return {"success": False, "error": "Failed to execute swap after multiple retries."}

    def get_historical_price(self, token_address: str, chainId: int, period: str) -> dict:
        """
        Fetches historical price data for a token.
        """
        for attempt in range(self.max_retries):
            try:
                request_path = '/api/v5/dex/historical-index-price'
                params = {
                    "chainId": chainId,
                    "tokenAddress": token_address,
                    "period": period
                }
                
                query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
                full_request_path = f"{request_path}?{query_string}"

                headers = self._get_request_headers('GET', full_request_path)
                url = f"{self.base_url}{full_request_path}"
                
                logger.info(f"Sending GET request to OKX for historical price: {url}")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == "0":
                    return {"success": True, "data": data.get("data", [{}])[0]}
                else:
                    error_msg = data.get("msg", "Unknown API error")
                    logger.error(f"Error fetching historical price from OKX API: {error_msg}")
                    return {"success": False, "error": f"API Error: {error_msg}"}
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP Error on attempt {attempt + 1}: {e}. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching historical price: {e}")
                return {"success": False, "error": f"A network error occurred: {e}"}
        
        return {"success": False, "error": "Failed to fetch historical price after multiple retries."}


if __name__ == '__main__':
    # Example usage to test API credentials
    print("Attempting to verify OKX API credentials with a DEX endpoint...")
    client = OKXClient()
    if not all([client.api_key, client.api_secret, client.passphrase]):
        print("OKX credentials not found in .env file.")
    else:
        # Using get_live_quote for verification now
        verification_result = client.get_live_quote(
            from_token_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            to_token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            amount="1"
        )
        if verification_result.get("success"):
            print("Successfully connected to OKX DEX API. Credentials are valid.")
        else:
            print(f"Failed to connect to OKX DEX API. Error: {verification_result.get('error')}")
