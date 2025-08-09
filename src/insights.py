import os
import google.generativeai as genai
import logging
from src.database import get_db_connection
from src.okx_client import OKXClient
from src.portfolio import PortfolioService

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
        self.portfolio_service = PortfolioService()

    def get_user_portfolio(self, user_id: int) -> dict:
        """Return a simplified snapshot of the user's portfolio from PortfolioService."""
        snap = self.portfolio_service.get_snapshot(user_id)
        if not snap or not snap.get("assets"):
            return {}
        # Convert to simple {symbol: quantity}
        return {a["symbol"]: a["quantity"] for a in snap.get("assets", [])}

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
            You are Esther, a friendly, concise crypto market copilot. Provide approachable insights for a user with the following portfolio:
            {portfolio}

            Market data:
            {market_data}

            Give a short analysis and 1–2 practical suggestions.
            Style: warm, encouraging, beginner‑friendly, but non‑promissory. Include a brief caution that this is not financial advice.
            """

            response = self.pro_model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating insights with Gemini Pro model: {e}")
            return "I'm sorry, I'm having trouble generating insights for you right now. Please try again later."
