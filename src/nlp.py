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
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        genai.configure(api_key=self.api_key)
        
        # Initialize both models as per the PRD and official documentation
        self.flash_model = genai.GenerativeModel('gemini-2.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-2.5-pro')

    def parse_intent(self, text: str, model_type: str = 'flash') -> dict:
        """
        Uses the specified Gemini model to parse the user's intent from a text message.
        :param text: The user's message.
        :param model_type: 'flash' or 'pro'. Defaults to 'flash'.
        """
        try:
            model = self.flash_model if model_type == 'flash' else self.pro_model
            
            prompt = f"""
            From the following user query, extract the intent and any relevant entities.
            The possible intents are: 'buy_token', 'sell_token', 'get_price', 'set_stop_loss', 'set_take_profit', 'greeting', 'help', 'unknown'.
            
            - For 'get_price', extract the 'symbol' (e.g., BTC, ETH).
            - For 'buy_token', extract 'amount', 'symbol', 'currency', and optionally 'source_chain' and 'destination_chain'.
            - For 'sell_token', extract 'amount', 'symbol', 'currency', and optionally 'source_chain' and 'destination_chain'.
            - For 'set_stop_loss', extract the 'symbol' and the 'price'.
            - For 'set_take_profit', extract the 'symbol' and the 'price'.

            Query: "{text}"

            Respond ONLY with a valid JSON object in the format {{"intent": "...", "entities": {{...}}}}.
            Example for get_price: {{"intent": "get_price", "entities": {{"symbol": "BTC"}}}}
            Example for buy_token: {{"intent": "buy_token", "entities": {{"amount": "0.5", "symbol": "ETH", "currency": "USDT"}}}}
            Example for cross-chain buy_token: {{"intent": "buy_token", "entities": {{"amount": "0.5", "symbol": "ETH", "currency": "USDC", "source_chain": "Arbitrum", "destination_chain": "Polygon"}}}}
            Example for sell_token: {{"intent": "sell_token", "entities": {{"amount": "10", "symbol": "SOL", "currency": "USDC"}}}}
            Example for set_stop_loss: {{"intent": "set_stop_loss", "entities": {{"symbol": "BTC", "price": "60000"}}}}
            Example for set_take_profit: {{"intent": "set_take_profit", "entities": {{"symbol": "ETH", "price": "3000"}}}}
            """
            
            response = model.generate_content(prompt)
            
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
