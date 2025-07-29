# Cross-Chain Swap Testing Guide

This guide provides detailed instructions on how to test the cross-chain swap functionality in the Esther AI Agent.

## 1. Overview

The cross-chain swap feature allows users to trade tokens between different blockchains (e.g., swapping ETH on Arbitrum for USDC on Polygon). This guide covers how to test the functionality to ensure it is working correctly.

## 2. Prerequisites

Before you begin, ensure you have the following:

- A configured `.env` file with your OKX API credentials.
- A wallet with funds on the test networks you intend to use.

## 3. Testing Procedures

Follow these steps to test the cross-chain swap functionality:

### Step 1: Test NLP Recognition

Verify that the NLP model correctly identifies the `source_chain` and `destination_chain` from user commands.

- **Run the NLP tests:**
  ```bash
  python -m unittest tests/test_nlp.py
  ```
- **Expected Outcome:** All tests should pass, confirming that the model can parse various cross-chain swap commands.

### Step 2: Test Core Logic

Ensure that the main application logic correctly handles the new chain information and calls the OKX client with the correct parameters.

- **Run the core logic tests:**
  ```bash
  python -m unittest tests/test_main.py
  ```
- **Expected Outcome:** All tests should pass, confirming that the `buy_token_intent` and `sell_token_intent` functions are working as expected.

### Step 3: Test OKX Client

Verify that the OKX client correctly includes the `chain_index` in the API requests.

- **Run the OKX client tests:**
  ```bash
  python -m unittest tests/test_okx_client.py
  ```
- **Expected Outcome:** All tests should pass, confirming that the `get_live_quote` and `execute_swap` functions are correctly sending the `chain_index` to the OKX DEX aggregator.

### Step 4: End-to-End Testing

Perform an end-to-end test to simulate a real user interaction.

1. **Run the application:**
   ```bash
   python run.py
   ```
2. **Interact with the bot:**
   - Send a command to perform a cross-chain swap, for example:
     ```
     /swap 0.01 ETH on arbitrum for USDC on polygon
     ```
   - The bot should respond with a confirmation message that includes the source and destination chains.
   - Confirm the swap.
3. **Verify the transaction:**
   - Check your wallet to ensure the swap was executed correctly.

## 4. Troubleshooting

- **NLP Errors:** If the NLP tests fail, review the prompt in `src/nlp.py` and ensure the examples are clear and cover a variety of use cases.
- **Core Logic Errors:** If the core logic tests fail, check the chain name to `chainIndex` mapping in `src/main.py` and ensure it is correct.
- **OKX Client Errors:** If the OKX client tests fail, review the `get_live_quote` and `execute_swap` functions in `src/okx_client.py` to ensure the `chain_index` is being correctly included in the API requests.

By following this guide, you can thoroughly test the cross-chain swap functionality and ensure it is working as expected.
