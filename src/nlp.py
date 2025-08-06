import os
import google.generativeai as genai
import logging
import json

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class NLPClient:
    """A client for interacting with the Gemini API for NLP tasks."""

    def __init__(self):
        """Initializes the NLP client by configuring the Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=api_key)
        
        # Use lazy initialization for the models
        self._flash_model = None
        self._pro_model = None

    @property
    def flash_model(self):
        """Lazy-loads and returns the Gemini Flash model."""
        if self._flash_model is None:
            self._flash_model = genai.GenerativeModel('gemini-2.5-flash')
        return self._flash_model

    @property
    def pro_model(self):
        """Lazy-loads and returns the Gemini Pro model."""
        if self._pro_model is None:
            self._pro_model = genai.GenerativeModel('gemini-2.5-pro')
        return self._pro_model

    def parse_intent(self, text: str, model_type: str = 'flash') -> dict:
        """
        Parses the user's intent from a text query using the specified Gemini model.
        """
        
        # This is a standard string template, not an f-string.
        prompt_template = """
        You are an AI assistant for a crypto trading bot. Your task is to understand the user's intent and extract relevant entities from their message.
        
        Based on the user's message, identify one of the following intents.
        - greeting: User says hello or similar.
        - get_price: User asks for the price of a token.
        - buy_token: User wants to buy a token.
        - sell_token: User wants to sell a token.
        - set_stop_loss: User wants to set a stop-loss order.
        - set_take_profit: User wants to set a take-profit order.
        - list_wallets: User wants to see their saved wallets.
        - add_wallet: User wants to add a new wallet.
        - show_portfolio: User wants to see their portfolio.
        - get_insights: User wants to get market or portfolio insights.
        
        For trading intents (buy, sell), extract the following entities if present:
        - symbol: The token symbol (e.g., ETH, BTC).
        - amount: The quantity of the token.
        - currency: The currency to use for the transaction.
        - source_chain: The source blockchain (if specified).
        - destination_chain: The destination blockchain (if specified).

        Return the output as a JSON object with "intent" and "entities" keys.

            Example for get_price: {{"intent": "get_price", "entities": {{"symbol": "BTC"}}}}
            Example for buy_token: {{"intent": "buy_token", "entities": {{"amount": "0.5", "symbol": "ETH", "currency": "USDT"}}}}
            Example for set_stop_loss: {{"intent": "set_stop_loss", "entities": {{"symbol": "BTC", "price": "60000"}}}}
            Example for set_take_profit: {{"intent": "set_take_profit", "entities": {{"symbol": "ETH", "price": "3000"}}}}
        Example for list_wallets: {{"intent": "list_wallets", "entities": {{}}}}
        Example for add_wallet: {{"intent": "add_wallet", "entities": {{}}}}
        Example for show_portfolio: {{"intent": "show_portfolio", "entities": {{}}}}
        Example for get_insights: {{"intent": "get_insights", "entities": {{}}}}

        Query: "{text}"
        """
        
        # Safely format the prompt with the user's text
        prompt = prompt_template.format(text=text)

        try:
            model = self.pro_model if model_type == 'pro' else self.flash_model
            response = model.generate_content(prompt)
            
            if not response.parts:
                logger.error(f"Gemini {model_type} model returned no content. Finish reason: {response.prompt_feedback}")
                return {"intent": "unknown", "entities": {}}

            # Clean up the response to ensure it's valid JSON
            json_response_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_response_text)

        except Exception as e:
            logger.error(f"Error parsing intent with Gemini {model_type} model: {e}")
            return {"intent": "unknown", "entities": {}}

if __name__ == '__main__':
    # Example usage
    nlp_client = NLPClient()
    
    query1 = "what is the price of btc?"
    intent1 = nlp_client.parse_intent(query1, model_type='flash')
    print(f"Query: '{query1}' (Flash) -> Intent: {intent1}")

    query2 = "buy 0.1 WBTC with my USDC"
    intent2 = nlp_client.parse_intent(query2, model_type='pro')
    print(f"Query: '{query2}' (Pro) -> Intent: {intent2}")
