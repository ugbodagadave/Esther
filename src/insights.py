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
        return {"ETH": 1.5, "USDC": 1000}

    def get_market_data(self) -> dict:
        """
        Retrieves market data from the OKX API.
        For now, we will just return dummy market data.
        """
        return {"ETH": {"price": 3000, "trend": "up"}, "BTC": {"price": 60000, "trend": "down"}}

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
