import os
import requests
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class OKXClient:
    def __init__(self):
        self.base_url = "https://web3.okx.com"
        self.api_key = os.getenv("OKX_API_KEY")
        self.api_secret = os.getenv("OKX_API_SECRET")
        self.passphrase = os.getenv("OKX_API_PASSPHRASE")

    def get_price(self, symbol: str) -> dict:
        """
        Fetches the current price of a trading pair from OKX.
        e.g. symbol='BTC-USDT'
        """
        try:
            # Using v5 public tickers endpoint
            url = f"https://www.okx.com/api/v5/market/ticker?instId={symbol.upper()}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                ticker_data = data.get("data", [{}])[0]
                return {
                    "symbol": symbol,
                    "price": ticker_data.get("last"),
                }
            else:
                logger.error(f"Error from OKX API: {data.get('msg')}")
                return {"error": data.get("msg")}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from OKX: {e}")
            return {"error": str(e)}

    def get_swap_quote(self, from_token: str, to_token: str, amount: str, chain_index: int = 1, slippage: float = 0.05) -> dict:
        """
        Fetches a swap quote from the OKX DEX aggregator.
        e.g., from_token='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', to_token='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', amount='10000000000000'
        """
        try:
            # This is a simplified example. A real implementation requires generating a valid signature.
            # The signature generation process is complex and involves HMAC-SHA256.
            # For now, we will mock the request and focus on the structure.
            
            # Placeholder for where signature generation would occur
            # timestamp = ...
            # sign = generate_signature(timestamp, method, request_path, body, self.api_secret)
            
            headers = {
                'OK-ACCESS-KEY': self.api_key,
                'OK-ACCESS-SIGN': "placeholder_sign",
                'OK-ACCESS-PASSPHRASE': self.passphrase,
                'OK-ACCESS-TIMESTAMP': "placeholder_timestamp",
                'Content-Type': 'application/json'
            }

            params = {
                "chainIndex": chain_index,
                "amount": amount,
                "toTokenAddress": to_token,
                "fromTokenAddress": from_token,
                "slippage": slippage,
                "userWalletAddress": "0x6f9ffea7370310cd0f890dfde5e0e061059dcfb8" # Example address
            }
            
            url = f"{self.base_url}/api/v5/dex/aggregator/swap"
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("code") == "0":
                return data.get("data", [{}])[0]
            else:
                logger.error(f"Error from OKX API: {data.get('msg')}")
                return {"error": data.get("msg")}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching swap quote from OKX: {e}")
            return {"error": str(e)}

if __name__ == '__main__':
    # This part is for demonstration and will not work without valid credentials and signature generation.
    print("OKX Client initialized. Note: Live calls require valid API credentials and signature generation.")
    # client = OKXClient()
    # quote = client.get_swap_quote(
    #     from_token='0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 
    #     to_token='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 
    #     amount='10000000000000'
    # )
    # print(quote)
