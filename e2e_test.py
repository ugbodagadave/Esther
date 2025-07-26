import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.nlp import NLPClient
from src.okx_client import OKXClient

def run_e2e_test():
    """
    Runs an end-to-end test to verify live API calls to Gemini and OKX.
    """
    print("--- Starting End-to-End API Test ---")
    
    # Load environment variables
    load_dotenv()
    
    # --- Test 1: Gemini API Call ---
    print("\n[1/2] Testing Gemini API connection and intent parsing...")
    try:
        nlp_client = NLPClient()
        test_query = "buy 0.01 eth with usdc"
        print(f"    Query: '{test_query}'")
        
        intent_data = nlp_client.parse_intent(test_query, model_type='pro')
        
        if intent_data and intent_data.get('intent') == 'buy_token':
            print("    ✅ SUCCESS: Gemini API responded and correctly parsed the 'buy_token' intent.")
            print(f"    -> Response: {intent_data}")
        else:
            print("    ❌ FAILURE: Did not receive a valid 'buy_token' intent from Gemini.")
            print(f"    -> Response: {intent_data}")
            
    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the Gemini API test: {e}")

    # --- Test 2: OKX DEX API Call ---
    print("\n[2/2] Testing OKX DEX API connection and credential verification...")
    try:
        okx_client = OKXClient()
        if not all([okx_client.api_key, okx_client.api_secret, okx_client.passphrase]):
            print("    ❌ FAILURE: OKX credentials not found in .env file.")
            return

        # We now test by fetching a live quote for a common pair
        print("    Query: Fetching a live quote for 1 USDC to ETH...")
        quote_result = okx_client.get_live_quote(
            from_token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", # USDC
            to_token_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",   # ETH
            amount="1000000" # 1 USDC (6 decimals)
        )
        
        if quote_result.get("success"):
            print("    ✅ SUCCESS: OKX DEX API responded with a valid quote. Credentials and connection are working.")
            print(f"    -> Quote Data: {quote_result.get('data')}")
        else:
            print("    ❌ FAILURE: OKX DEX API returned an error while fetching quote.")
            print(f"    -> Error: {quote_result.get('error')}")

    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the OKX DEX API test: {e}")
        
    print("\n--- End-to-End Test Finished ---")


if __name__ == "__main__":
    run_e2e_test()
