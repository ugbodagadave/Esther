import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.nlp import NLPClient
from src.okx_client import OKXClient
from src.okx_explorer import OKXExplorer
from src.portfolio import PortfolioService
from src.database import initialize_database, get_db_connection
from src.encryption import encrypt_data
import traceback


def run_e2e_test():
    """
    Runs an end-to-end test to verify live API calls to Gemini and OKX.
    """
    print("--- Starting End-to-End API Test ---")
    
    # Load environment variables
    load_dotenv()
    
    # --- Test 1: Gemini API Call (Buy Intent) ---
    print("\n[1/6] Testing Gemini API connection and 'buy_token' intent parsing...")
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

    # --- Test 2: Gemini API Call (Sell Intent) ---
    print("\n[2/6] Testing Gemini API connection and 'sell_token' intent parsing...")
    try:
        nlp_client = NLPClient()
        test_query = "sell 0.5 eth for usdt"
        print(f"    Query: '{test_query}'")
        
        intent_data = nlp_client.parse_intent(test_query, model_type='pro')
        
        if intent_data and intent_data.get('intent') == 'sell_token':
            print("    ✅ SUCCESS: Gemini API responded and correctly parsed the 'sell_token' intent.")
            print(f"    -> Response: {intent_data}")
        else:
            print("    ❌ FAILURE: Did not receive a valid 'sell_token' intent from Gemini.")
            print(f"    -> Response: {intent_data}")
            
    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the Gemini API test: {e}")

    # --- Test 3: OKX DEX API Quote Call ---
    print("\n[3/6] Testing OKX DEX API connection and quote functionality...")
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

    # --- Test 4: OKX DEX API Swap Simulation Call ---
    print("\n[4/6] Testing OKX DEX API swap simulation...")
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

    # --- Test 5: OKX DEX Balance Endpoint ---
    print("\n[5/6] Testing OKX DEX balance endpoint...")
    try:
        explorer_client = OKXExplorer()
        wallet_address = os.getenv("TEST_WALLET_ADDRESS")
        if not wallet_address:
            print("    ❌ FAILURE: TEST_WALLET_ADDRESS not found in .env file.")
        else:
            print(f"    Query: Fetching all balances for {wallet_address} on ETH & BSC...")
            balance_result = explorer_client.get_all_balances(wallet_address, chains=[1, 56]) # ETH, BSC
            if balance_result.get("success"):
                print("    ✅ SUCCESS: OKX DEX balance API responded successfully.")
                print(f"    -> Response Data: {balance_result.get('data')}")
            else:
                print("    ❌ FAILURE: OKX DEX balance API returned an error.")
                print(f"    -> Error: {balance_result.get('error')}")

    except Exception as e:
        print(f"    ❌ FAILURE: An exception occurred during the OKX DEX balance test: {e}")

    # --- Test 6: Portfolio Sync & Snapshot ---
    print("\n[6/6] Testing Portfolio Sync, Snapshot, and Analytics...")

    try:
        # This test requires a wallet address and its private key for setup
        test_wallet_address = os.getenv("TEST_WALLET_ADDRESS")
        test_wallet_pk = os.getenv("TEST_WALLET_PRIVATE_KEY")
        if not test_wallet_address or not test_wallet_pk:
            print("    ❌ FAILURE: TEST_WALLET_ADDRESS and TEST_WALLET_PRIVATE_KEY must be in .env for this test.")
            return

        # Ensure tables exist (this implicitly tests the migration)
        initialize_database()

        # We need a db connection to set up the test data
        conn = get_db_connection()
        if not conn:
            print("    ❌ FAILURE: Could not connect to the database for portfolio test setup.")
            return

        dummy_telegram_id = 999999999
        with conn.cursor() as cur:
            # Clean up previous test runs to ensure idempotency
            cur.execute("DELETE FROM users WHERE telegram_id = %s;", (dummy_telegram_id,))
            conn.commit()

            # Create a dummy user
            cur.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id;", (dummy_telegram_id, 'e2e_tester'))
            user_pk = cur.fetchone()[0]

            # Add a wallet for the user (chain_id 1 = Ethereum)
            encrypted_sk = encrypt_data(test_wallet_pk)
            cur.execute(
                "INSERT INTO wallets (user_id, name, address, encrypted_private_key, chain_id) VALUES (%s, %s, %s, %s, %s);",
                (user_pk, 'e2e_test_wallet', test_wallet_address, encrypted_sk, 1)
            )
            conn.commit()
        conn.close()

        # Now, execute the service logic
        portfolio_service = PortfolioService()

        print(f"    Query: Syncing balances for user {dummy_telegram_id} with wallet {test_wallet_address}")
        synced = portfolio_service.sync_balances(dummy_telegram_id)
        if not synced:
            raise Exception("portfolio_service.sync_balances returned False")

        print("    Query: Retrieving portfolio snapshot...")
        snapshot = portfolio_service.get_snapshot(dummy_telegram_id)

        if snapshot and "total_value_usd" in snapshot and snapshot.get("assets"):
            print(f"    ✅ SUCCESS: Portfolio sync and snapshot retrieved successfully.")
            print(f"    -> Snapshot Total Value: ${snapshot['total_value_usd']:.2f}")
            print(f"    -> Assets Found: {len(snapshot.get('assets', []))}")

            # Also test analytics functions
            div = portfolio_service.get_diversification(dummy_telegram_id)
            print(f"    -> Diversification: {div}")

            roi = portfolio_service.get_roi(dummy_telegram_id, window_days=7)
            print(f"    -> 7-day ROI: {roi*100:.2f}%")
        else:
            print("    ❌ FAILURE: Snapshot data was empty or invalid after a successful sync.")
            print(f"    -> Snapshot: {snapshot}")

    except Exception as e:
        print(f"    ❌ FAILURE: Portfolio tests encountered an error: {e}")
        traceback.print_exc()

    # --- Test 7: Conversational NLP ---
    print("\n[7/7] Testing conversational NLP intents...")
    try:
        nlp_client = NLPClient()
        
        # Test "list_wallets"
        print("    Query: 'show me my wallets'")
        intent_data = nlp_client.parse_intent("show me my wallets")
        if intent_data.get('intent') == 'list_wallets':
            print("    ✅ SUCCESS: Correctly parsed 'list_wallets' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'list_wallets'. Got: {intent_data}")

        # Test "add_wallet"
        print("    Query: 'I want to add a wallet'")
        intent_data = nlp_client.parse_intent("I want to add a wallet")
        if intent_data.get('intent') == 'add_wallet':
            print("    ✅ SUCCESS: Correctly parsed 'add_wallet' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'add_wallet'. Got: {intent_data}")
            
        # Test "show_portfolio"
        print("    Query: 'what is in my portfolio'")
        intent_data = nlp_client.parse_intent("what is in my portfolio")
        if intent_data.get('intent') == 'show_portfolio':
            print("    ✅ SUCCESS: Correctly parsed 'show_portfolio' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'show_portfolio'. Got: {intent_data}")
            
    except Exception as e:
        print(f"    ❌ FAILURE: Conversational NLP tests encountered an error: {e}")
        traceback.print_exc()

    print("\n--- End-to-End Test Finished ---")


if __name__ == "__main__":
    run_e2e_test()
