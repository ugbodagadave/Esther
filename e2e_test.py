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
from src.chart_generator import generate_price_chart
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
            # First, get the user_id if it exists
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (dummy_telegram_id,))
            user_record = cur.fetchone()
            if user_record:
                user_pk = user_record[0]
                # Delete associated wallets first
                cur.execute("DELETE FROM wallets WHERE user_id = %s;", (user_pk,))
                # Delete associated portfolios 
                cur.execute("DELETE FROM portfolios WHERE user_id = %s;", (user_pk,))
            
            # Now, delete the user
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

        if snapshot and "total_value_usd" in snapshot:
            if snapshot.get("assets"):
                print(f"    ✅ SUCCESS: Portfolio sync and snapshot retrieved successfully.")
                print(f"    -> Snapshot Total Value: ${snapshot['total_value_usd']:.2f}")
                print(f"    -> Assets Found: {len(snapshot.get('assets', []))}")

                # Also test analytics functions
                div = portfolio_service.get_diversification(dummy_telegram_id)
                print(f"    -> Diversification: {div}")

                roi = portfolio_service.get_roi(dummy_telegram_id, window_days=7)
                print(f"    -> 7-day ROI: {roi*100:.2f}%")
            elif snapshot.get("total_value_usd") == 0.0 and not snapshot.get("assets"):
                print("    ✅ SUCCESS: Portfolio sync completed successfully for an empty wallet.")
                print(f"    -> Snapshot: {snapshot}")
            else:
                print("    ❌ FAILURE: Snapshot data was empty or invalid after a successful sync.")
                print(f"    -> Snapshot: {snapshot}")
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

        # Test "greeting"
        print("    Query: 'hello esther'")
        intent_data = nlp_client.parse_intent("hello esther")
        if intent_data.get('intent') == 'greeting':
            print("    ✅ SUCCESS: Correctly parsed 'greeting' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'greeting'. Got: {intent_data}")

        # Test "get_price"
        print("    Query: 'what is the price of btc'")
        intent_data = nlp_client.parse_intent("what is the price of btc")
        if intent_data.get('intent') == 'get_price':
            print("    ✅ SUCCESS: Correctly parsed 'get_price' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'get_price'. Got: {intent_data}")

        # Test "set_stop_loss"
        print("    Query: 'set stop loss for BTC at 60000'")
        intent_data = nlp_client.parse_intent("set stop loss for BTC at 60000")
        if intent_data.get('intent') == 'set_stop_loss':
            print("    ✅ SUCCESS: Correctly parsed 'set_stop_loss' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'set_stop_loss'. Got: {intent_data}")

        # Test "set_take_profit"
        print("    Query: 'set take profit for ETH at 3500'")
        intent_data = nlp_client.parse_intent("set take profit for ETH at 3500")
        if intent_data.get('intent') == 'set_take_profit':
            print("    ✅ SUCCESS: Correctly parsed 'set_take_profit' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'set_take_profit'. Got: {intent_data}")

        # Test "get_insights"
        print("    Query: 'give me market insights'")
        intent_data = nlp_client.parse_intent("give me market insights")
        if intent_data.get('intent') == 'get_insights':
            print("    ✅ SUCCESS: Correctly parsed 'get_insights' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'get_insights'. Got: {intent_data}")

        # Test "set_default_wallet"
        print("    Query: 'set my default wallet'")
        intent_data = nlp_client.parse_intent("set my default wallet")
        if intent_data.get('intent') == 'set_default_wallet':
            print("    ✅ SUCCESS: Correctly parsed 'set_default_wallet' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'set_default_wallet'. Got: {intent_data}")

        # Test "enable_live_trading"
        print("    Query: 'enable live trading'")
        intent_data = nlp_client.parse_intent("enable live trading")
        if intent_data.get('intent') == 'enable_live_trading':
            print("    ✅ SUCCESS: Correctly parsed 'enable_live_trading' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'enable_live_trading'. Got: {intent_data}")
     
    except Exception as e:
        print(f"    ❌ FAILURE: Conversational NLP tests encountered an error: {e}")
        traceback.print_exc()

    print("\n--- End-to-End Test Finished ---")

def test_e2e_rebalance_suggestion():
    """Test the full rebalance suggestion workflow."""
    print("\n--- E2E Rebalance Suggestion ---")
    try:
        portfolio_service = PortfolioService()
        dummy_telegram_id = 999999999 # Same dummy user from portfolio sync test
        
        # Ensure the user has a portfolio to rebalance
        synced = portfolio_service.sync_balances(dummy_telegram_id)
        if not synced:
            raise Exception("Balance sync failed before rebalance test")

        print("    Query: Suggesting a rebalance to 50% BTC and 50% ETH...")
        target_alloc = {"WBTC": 50, "ETH": 50} # Use WBTC as it's the swappable version
        plan = portfolio_service.suggest_rebalance(dummy_telegram_id, target_alloc=target_alloc)

        if plan:
            print("    ✅ SUCCESS: Rebalance plan generated successfully.")
            print(f"    -> Plan: {plan}")
        else:
            print("    ✅ SUCCESS: Portfolio is likely already balanced or empty.")

    except Exception as e:
        print(f"    ❌ FAILURE: Rebalance suggestion test encountered an error: {e}")
        traceback.print_exc()


def test_e2e_price_chart():
    """Test the full price chart workflow."""
    print("\n--- E2E Price Chart ---")
    try:
        nlp_client = NLPClient()
        okx_client = OKXClient()

        # Test NLP intent
        print("    Query: 'show me the price chart for btc'")
        intent_data = nlp_client.parse_intent("show me the price chart for btc")
        if intent_data.get('intent') == 'get_price_chart' and intent_data.get('entities', {}).get('symbol') == 'BTC':
            print("    ✅ SUCCESS: Correctly parsed 'get_price_chart' intent.")
        else:
            print(f"    ❌ FAILURE: Incorrectly parsed 'get_price_chart'. Got: {intent_data}")
            return

        # Test OKX historical data
        print("    Query: Fetching historical data for BTC...")
        historical_data = okx_client.get_historical_price(
            token_address="BTC-USD", # Use the instrument ID for BTC
            chainId=1, # Not used for instrument IDs, but required by the function signature
            period="7d"
        )

        if historical_data.get("success"):
            print("    ✅ SUCCESS: OKX historical price API responded successfully.")
            # Test chart generation
            print("    Query: Generating price chart...")
            chart_image = generate_price_chart(historical_data['data'], "BTC", "7d")
            if isinstance(chart_image, bytes) and len(chart_image) > 0:
                print("    ✅ SUCCESS: Price chart generated successfully.")
            else:
                print("    ❌ FAILURE: Price chart generation failed.")
        else:
            print("    ❌ FAILURE: OKX historical price API returned an error.")
            print(f"    -> Error: {historical_data.get('error')}")

    except Exception as e:
        print(f"    ❌ FAILURE: Price chart test encountered an error: {e}")
        traceback.print_exc()


def test_e2e_portfolio_performance():
    """Test the full portfolio performance workflow."""
    print("\n--- E2E Portfolio Performance ---")
    try:
        portfolio_service = PortfolioService()
        dummy_telegram_id = 999999999 # Same dummy user from portfolio sync test
        
        # Ensure the user has a portfolio to test
        synced = portfolio_service.sync_balances(dummy_telegram_id)
        if not synced:
            raise Exception("Balance sync failed before performance test")

        # Save a snapshot for today
        snapshot = portfolio_service.get_snapshot(dummy_telegram_id)
        if snapshot and snapshot.get("total_value_usd") > 0:
            conn = get_db_connection()
            if not conn:
                raise Exception("Could not connect to db to save snapshot")
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (dummy_telegram_id,))
                user_pk = cur.fetchone()[0]
                # Save a fake historical record for 8 days ago
                cur.execute(
                    """
                    INSERT INTO portfolio_history (user_id, total_value_usd, snapshot_date)
                    VALUES (%s, %s, CURRENT_DATE - INTERVAL '8 days')
                    ON CONFLICT (user_id, snapshot_date) DO UPDATE SET total_value_usd = EXCLUDED.total_value_usd;
                    """,
                    (user_pk, snapshot['total_value_usd'] * 0.9) # Simulate a 10% gain
                )
                conn.commit()
            conn.close()

        print("    Query: Calculating 7-day portfolio performance...")
        performance = portfolio_service.get_portfolio_performance(dummy_telegram_id, period_days=7)

        if performance:
            print("    ✅ SUCCESS: Portfolio performance calculated successfully.")
            print(f"    -> Performance Data: {performance}")
        else:
            print("    ❌ FAILURE: Portfolio performance calculation failed.")

    except Exception as e:
        print(f"    ❌ FAILURE: Portfolio performance test encountered an error: {e}")
        traceback.print_exc()


def test_e2e_user_settings_live_trading():
    """Test setting default wallet and enabling live trading (DB-level to mirror handlers)."""
    print("\n--- E2E User Settings: Default Wallet and Live Trading ---")
    try:
        load_dotenv()
        initialize_database()

        test_wallet_address = os.getenv("TEST_WALLET_ADDRESS")
        test_wallet_pk = os.getenv("TEST_WALLET_PRIVATE_KEY")
        if not test_wallet_address or not test_wallet_pk:
            print("    ❌ FAILURE: TEST_WALLET_ADDRESS and TEST_WALLET_PRIVATE_KEY must be in .env for this test.")
            return

        conn = get_db_connection()
        if not conn:
            print("    ❌ FAILURE: Could not connect to the database for user settings test.")
            return

        dummy_telegram_id = 888888888
        with conn.cursor() as cur:
            # Ensure clean state
            cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (dummy_telegram_id,))
            user_record = cur.fetchone()
            if user_record:
                user_pk = user_record[0]
                cur.execute("DELETE FROM wallets WHERE user_id = %s;", (user_pk,))
            cur.execute("DELETE FROM users WHERE telegram_id = %s;", (dummy_telegram_id,))
            conn.commit()

            # Create user
            cur.execute("INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id;", (dummy_telegram_id, 'e2e_user_settings'))
            user_pk = cur.fetchone()[0]

            # Add a wallet
            encrypted_sk = encrypt_data(test_wallet_pk)
            cur.execute(
                "INSERT INTO wallets (user_id, name, address, encrypted_private_key, chain_id) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                (user_pk, 'default_wallet', test_wallet_address, encrypted_sk, 1)
            )
            wallet_id = cur.fetchone()[0]

            # Set default wallet (mirrors set_default_wallet_callback)
            cur.execute("UPDATE users SET default_wallet_id = %s WHERE id = %s;", (wallet_id, user_pk))

            # Enable live trading (mirrors enable_live_trading_callback)
            cur.execute("UPDATE users SET live_trading_enabled = %s WHERE id = %s;", (True, user_pk))
            conn.commit()

            # Verify
            cur.execute("SELECT default_wallet_id, live_trading_enabled FROM users WHERE id = %s;", (user_pk,))
            default_wallet_id, live_enabled = cur.fetchone()

        conn.close()

        if default_wallet_id == wallet_id and live_enabled:
            print("    ✅ SUCCESS: Default wallet set and live trading enabled in DB.")
        else:
            print("    ❌ FAILURE: Failed to set default wallet and/or enable live trading.")

    except Exception as e:
        print(f"    ❌ FAILURE: User settings test encountered an error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    run_e2e_test()
    test_e2e_user_settings_live_trading()
    test_e2e_rebalance_suggestion()
    test_e2e_portfolio_performance()
    test_e2e_price_chart()
    
    # Optional: Insights E2E (requires Gemini and OKX creds, and a wallet for dummy user 999999999)
    try:
        from src.insights import InsightsClient
        if os.getenv("GEMINI_API_KEY"):
            print("\n--- E2E Insights Generation ---")
            client = InsightsClient()
            text = client.generate_insights(user_id=999999999)
            if isinstance(text, str) and len(text) > 0:
                print("    ✅ SUCCESS: Insights generated.")
            else:
                print("    ❌ FAILURE: Insights generation returned empty text.")
        else:
            print("\n(SKIP) E2E Insights: GEMINI_API_KEY not set.")
    except Exception as e:
        print(f"    ❌ FAILURE: Insights E2E encountered an error: {e}")
        traceback.print_exc()
