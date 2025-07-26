import os
import requests
import logging
import hmac
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv

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
        self.base_url = "https://web3.okx.com"
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

    def get_live_quote(self, from_token_address: str, to_token_address: str, amount: str, chain_index: int = 1) -> dict:
        """
        Fetches a real swap quote from the OKX DEX aggregator.
        """
        try:
            request_path = '/api/v5/dex/aggregator/quote'
            params = {
                "chainIndex": chain_index,
                "amount": amount,
                "toTokenAddress": to_token_address,
                "fromTokenAddress": from_token_address
            }
            
            query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
            full_request_path = f"{request_path}?{query_string}"

            headers = self._get_request_headers('GET', full_request_path)
            url = f"{self.base_url}{full_request_path}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                return {"success": True, "data": data.get("data", [{}])[0]}
            else:
                logger.error(f"Error fetching quote from OKX API: {data.get('msg')}")
                return {"success": False, "error": data.get("msg")}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching quote: {e}")
            return {"success": False, "error": str(e)}

    def execute_swap(self, from_token_address: str, to_token_address: str, amount: str, wallet_address: str, slippage: str = "1", dry_run: bool = True) -> dict:
        """
        Executes a swap. If dry_run is True, it only fetches the quote and simulates the transaction.
        If dry_run is False, it executes a real swap on the blockchain.
        """
        if dry_run:
            logger.info(f"Executing DRY RUN swap from {from_token_address} to {to_token_address}")
            quote_response = self.get_live_quote(from_token_address, to_token_address, amount)
            
            if quote_response.get("success"):
                return {
                    "success": True,
                    "status": "simulated",
                    "data": quote_response["data"],
                    "message": "✅ Swap simulated successfully (no real transaction)"
                }
            else:
                return quote_response # Propagate the error from get_live_quote
        else:
            logger.info(f"Executing REAL swap for wallet {wallet_address}")
            try:
                request_path = '/api/v5/dex/aggregator/swap'
                body = {
                    "fromTokenAddress": from_token_address,
                    "toTokenAddress": to_token_address,
                    "amount": amount,
                    "walletAddress": wallet_address,
                    "slippage": slippage,
                    "chainIndex": 1
                }
                
                headers = self._get_request_headers('POST', request_path, str(body))
                url = f"{self.base_url}{request_path}"
                
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()
                data = response.json()

                if data.get("code") == "0":
                    logger.info(f"Successfully executed swap: {data.get('msg')}")
                    return {"success": True, "data": data.get("data", [{}])[0]}
                else:
                    logger.error(f"Error executing swap on OKX API: {data.get('msg')}")
                    return {"success": False, "error": data.get("msg")}
            except requests.exceptions.RequestException as e:
                logger.error(f"Error executing swap: {e}")
                return {"success": False, "error": str(e)}


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
