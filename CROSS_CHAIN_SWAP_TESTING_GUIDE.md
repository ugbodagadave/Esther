# How to Test Cross-Chain Swaps

Here's how you can test the new cross-chain swap feature:

### 1. Running the Bot

First, ensure the bot is running locally by executing the following command in your terminal:

```bash
python src/main.py
```

### 2. Testing in Your Telegram Chat

Once the bot is running, you can interact with it in your Telegram chat. Here are a few example prompts you can use to test the cross-chain swap functionality:

- **Swap ETH on Arbitrum for USDC on Polygon:**
  ```
  swap 0.01 ETH on Arbitrum for USDC on Polygon
  ```

- **Swap WBTC on Polygon for ETH on Ethereum:**
  ```
  swap 0.005 WBTC on Polygon for ETH on Ethereum
  ```

- **Sell ETH on Arbitrum for USDT on Arbitrum (same-chain):**
  ```
  sell 0.02 ETH on Arbitrum for USDT on Arbitrum
  ```

### What to Expect

1.  **Confirmation Message:** After you send a command, Esther will reply with a confirmation message that includes the source and destination chains, along with the estimated amount you will receive.
2.  **Confirm or Cancel:** You will see "✅ Confirm" and "❌ Cancel" buttons.
3.  **Execution:**
    - If you click "✅ **Confirm**", the swap will be executed (or simulated, depending on your `DRY_RUN_MODE` setting).
    - If you click "❌ **Cancel**", the operation will be aborted.

This will allow you to fully test the new cross-chain swap feature.
