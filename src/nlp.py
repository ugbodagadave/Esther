import os
import google.generativeai as genai
import logging

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
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def parse_intent(self, text: str) -> dict:
        """
        Uses Gemini Flash to parse the user's intent from a text message.
        """
        try:
            # A more sophisticated implementation would use few-shot prompting
            # or a more structured approach. For now, we use a simple prompt.
            prompt = f"""
            From the following user query, extract the intent and any relevant entities.
            The possible intents are: 'get_price', 'greeting', 'help', 'unknown'.
            If the intent is 'get_price', the entity should be the token symbol (e.g., BTC, ETH).

            Query: "{text}"

            Respond in JSON format with "intent" and "entities" keys.
            For example: {{"intent": "get_price", "entities": {{"symbol": "BTC"}}}}
            """
            
            response = self.model.generate_content(prompt)
            
            # Basic parsing of the JSON response from the model
            # A robust implementation would have better error handling here
            import json
            json_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(json_response)

        except Exception as e:
            logger.error(f"Error parsing intent with Gemini: {e}")
            return {"intent": "unknown", "entities": {}}

if __name__ == '__main__':
    # Example usage
    nlp_client = NLPClient()
    
    query1 = "what is the price of btc?"
    intent1 = nlp_client.parse_intent(query1)
    print(f"Query: '{query1}' -> Intent: {intent1}")

    query2 = "hello there"
    intent2 = nlp_client.parse_intent(query2)
    print(f"Query: '{query2}' -> Intent: {intent2}")
