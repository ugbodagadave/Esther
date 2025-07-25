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
        self.base_url = "https://www.okx.com"

    def get_price(self, symbol: str) -> dict:
        """
        Fetches the current price of a trading pair from OKX.
        e.g. symbol='BTC-USDT'
        """
        try:
            # Using v5 public tickers endpoint
            url = f"{self.base_url}/api/v5/market/ticker?instId={symbol.upper()}"
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            if data.get("code") == "0":
                ticker_data = data.get("data", [{}])[0]
                return {
                    "symbol": symbol,
                    "price": ticker_data.get("last"),
                    "volume_24h": ticker_data.get("vol24h")
                }
            else:
                logger.error(f"Error from OKX API: {data.get('msg')}")
                return {"error": data.get("msg")}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price from OKX: {e}")
            return {"error": str(e)}

if __name__ == '__main__':
    # Example usage
    client = OKXClient()
    price_data = client.get_price("BTC-USDT")
    if "error" not in price_data:
        print(f"The current price of BTC-USDT is: ${price_data['price']}")
    else:
        print(f"An error occurred: {price_data['error']}")

    price_data_eth = client.get_price("ETH-USDT")
    if "error" not in price_data_eth:
        print(f"The current price of ETH-USDT is: ${price_data_eth['price']}")
    else:
        print(f"An error occurred: {price_data_eth['error']}")
