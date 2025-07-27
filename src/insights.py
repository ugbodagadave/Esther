import os
import google.generativeai as genai
import logging
from src.database import get_db_connection
from src.okx_client import OKXClient

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class InsightsClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=self.api_key)
        self.pro_model = genai.GenerativeModel('gemini-2.5-pro')
        self.okx_client = OKXClient()

    def get_user_portfolio(self, user_id: int) -> dict:
        """
        Retrieves a user's portfolio from the database.
        In a real application, this would involve fetching token balances from the blockchain.
        For now, we will just return a dummy portfolio.
        """
        conn = get_db_connection()
        if conn is None:
            return {}

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (user_id,))
                user_id = cur.fetchone()[0]

                # This is a simplified portfolio representation.
                # In a real app, you would fetch token balances from the blockchain.
                cur.execute("SELECT name FROM wallets WHERE user_id = %s;", (user_id,))
                wallets = cur.fetchall()
                if wallets:
                    return {"ETH": 1.5, "USDC": 1000}
                else:
                    return {}
        except Exception as e:
            logger.error(f"Error fetching portfolio for user {user_id}: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def get_market_data(self) -> dict:
        """
        Retrieves market data from the OKX API.
        """
        # In a real app, you would fetch a variety of market data.
        # For now, we will just fetch the price of ETH and BTC.
        eth_price_response = self.okx_client.get_live_quote(
            from_token_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            to_token_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            amount="1000000000000000000"
        )
        btc_price_response = self.okx_client.get_live_quote(
            from_token_address="0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            to_token_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
            amount="100000000"
        )

        market_data = {}
        if eth_price_response.get("success"):
            price_estimate = float(eth_price_response["data"].get('toTokenAmount', 0)) / 1_000_000
            market_data["ETH"] = {"price": price_estimate, "trend": "up"}
        if btc_price_response.get("success"):
            price_estimate = float(btc_price_response["data"].get('toTokenAmount', 0)) / 1_000_000
            market_data["BTC"] = {"price": price_estimate, "trend": "down"}
            
        return market_data

    def generate_insights(self, user_id: int) -> str:
        """
        Generates personalized market insights for a user.
        """
        try:
            portfolio = self.get_user_portfolio(user_id)
            market_data = self.get_market_data()

            prompt = f"""
            As an expert crypto market analyst, provide personalized insights for a user with the following portfolio:
            {portfolio}

            Here is the current market data:
            {market_data}

            Based on the user's portfolio and the current market trends, provide a brief analysis and one or two actionable recommendations.
            Keep the tone professional, informative, and cautious. Do not give financial advice.
            """

            response = self.pro_model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating insights with Gemini Pro model: {e}")
            return "I'm sorry, I'm having trouble generating insights for you right now. Please try again later."
