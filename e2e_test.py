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

    # --- Test 2: OKX DEX API Quote Call ---
    print("\n[2/3] Testing OKX DEX API connection and quote functionality...")
    okx_client = OKXClient()
    if not all([okx_client.api_key, okx_client.api_secret, okx_client.passphrase]):
        print("    ❌ FAILURE: OKX credentials not found in .env file.")
        return

    try:
        print("    Query: Fetching a live quote for 1 USDC to ETH...")
        quote_result = okx_client.get_live_quote(
            from_token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", # USDC
            to_token_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",   # ETH
            amount="1000000" # 1 USDC (6 decimals)
        )
        
        if quote_result.get("success"):
            print("    ✅ SUCCESS: OKX DEX API responded with a valid quote.")
            print(f"    -> Quote Data: {quote_result.get('data')}")
        else:
            print("    ❌ FAILURE: OKX DEX API returned an error while fetching quote.")
            print(f"    -> Error: {quote_result.get('error')}")

    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the OKX DEX quote test: {e}")

    # --- Test 3: OKX DEX API Swap Simulation Call ---
    print("\n[3/3] Testing OKX DEX API swap simulation...")
    try:
        wallet_address = os.getenv("TEST_WALLET_ADDRESS")
        if not wallet_address:
            print("    ❌ FAILURE: TEST_WALLET_ADDRESS not found in .env file.")
            return

        print(f"    Query: Simulating a swap of 1 USDC to ETH for wallet {wallet_address}...")
        swap_result = okx_client.execute_swap(
            from_token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", # USDC
            to_token_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",   # ETH
            amount="1000000", # 1 USDC (6 decimals)
            wallet_address=wallet_address,
            dry_run=True # Explicitly keep this as a dry run for safety
        )

        if swap_result.get("success") and swap_result.get("status") == "simulated":
            print("    ✅ SUCCESS: OKX DEX API successfully simulated the swap.")
            print(f"    -> Simulated Swap Data: {swap_result.get('data')}")
        else:
            print("    ❌ FAILURE: OKX DEX API returned an error during swap simulation.")
            print(f"    -> Error: {swap_result.get('error')}")

    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the OKX DEX swap simulation test: {e}")

    print("\n--- End-to-End Test Finished ---")


if __name__ == "__main__":
    run_e2e_test()
