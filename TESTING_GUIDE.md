# Esther Bot Testing Guide

Here is a comprehensive guide to testing the Esther bot's features using natural language prompts.

---

### 1. Basic Interaction

**Test 1: Start Command**
*   **Your Message:** `/start`
*   **Expected Bot Response:** A welcome message from Esther, introducing herself and offering to help. For example: "Hello! I'm Esther, your AI-powered DEX trading assistant. I can help you check prices, execute trades, and get market insights. How can I help you today?"

**Test 2: Help Command**
*   **Your Message:** `/help`
*   **Expected Bot Response:** A message listing the main commands and features Esther supports, such as checking prices, trading, managing wallets, and getting insights.

---

### 2. Price Checks

**Test 1: Price of BTC**
*   **Your Message:** `What's the price of BTC?`
*   **Expected Bot Response:** A message showing the current price of Bitcoin (BTC) in USD or USDT. For example: "The current price of Bitcoin (BTC) is $113,722."

**Test 2: Price of ETH**
*   **Your Message:** `How much is ETH worth?`
*   **Expected Bot Response:** A message showing the current price of Ethereum (ETH). For example: "The current price of Ethereum (ETH) is $3,578."

**Test 3: Price of unsupported token**
*   **Your Message:** `What's the price of FOO?`
*   **Expected Bot Response:** A message indicating that the token is not supported. For example: "Sorry, I don't have the address for the token FOO."

---

### 3. Wallet Management

**Test 1: Show Wallets**
*   **Your Message:** `Show me my wallets`
*   **Expected Bot Response:** A list of your saved wallet addresses. If no wallets are added, it should prompt you to add one. For example: "Here are your saved wallets:\n- 0x123...abc\n- 0x456...def" or "You haven't added any wallets yet. Would you like to add one?"

**Test 2: Add a New Wallet**
*   **Your Message:** `I want to add a new wallet`
*   **Expected Bot Response:** Esther will guide you through a conversational flow to get the wallet name and address. It will then present a button to open a secure web app where you can enter your private key. Upon submission, the bot will confirm that the wallet has been saved.

**Test 3: Set Default Wallet**
*   **Your Message:** `/setdefaultwallet`
*   **Expected Bot Response:** A list of your saved wallets with buttons to select one as the default for trading. After selection, a confirmation message should appear.

**Test 4: Enable Live Trading**
*   **Your Message:** `/enablelivetrading`
*   **Expected Bot Response:** A message showing the current status of live trading (enabled/disabled) with buttons to change the setting. After selection, a confirmation message should appear.

---

### 4. Trading (Buy, Sell, Swap)

**Test 1: Buy ETH**
*   **Your Message:** `Buy 0.1 ETH with USDT`
*   **Expected Bot Response:**
    1.  A confirmation message showing the estimated amount of ETH you will receive for your USDT.
    2.  Two buttons: "✅ Confirm" and "❌ Cancel".
    3.  After confirming, a message indicating that the simulated trade was successful.

**Test 2: Sell ETH**
*   **Your Message:** `Sell 0.5 ETH for USDC`
*   **Expected Bot Response:** A similar confirmation flow as the "buy" command, ending with a success message for the simulated sale.

---

### 5. Cross-Chain Swaps

**Test 1: Swap ETH on Ethereum for MATIC on Polygon**
*   **Your Message:** `Swap 0.1 ETH on Ethereum for MATIC on Polygon`
*   **Expected Bot Response:** A confirmation message that clearly states the source chain (Ethereum) and destination chain (Polygon), along with the estimated amounts for the swap. The rest of the flow is the same as a regular trade.

---

### 6. Advanced Orders

**Test 1: Set Stop Loss**
*   **Your Message:** `Set a stop loss for BTC at 110000`
*   **Expected Bot Response:** A confirmation message like, "OK, I've set a stop-loss for BTC at $110,000. I will notify you if the price drops to this level."

**Test 2: Set Take Profit**
*   **Your Message:** `Set a take profit for ETH at 3700`
*   **Expected Bot Response:** A confirmation message like, "Got it. I've set a take-profit for ETH at $3,700."

---

### 7. Portfolio Tracking

**Test 1: Show Portfolio**
*   **Your Message:** `/portfolio` or `Show me my assets`
*   **Expected Bot Response:** A formatted message showing a list of all tokens in your wallet, their quantities, and their current value in USD, along with a total portfolio value.

**Test 2: Portfolio Performance**
*   **Your Message:** `How has my portfolio performed over the last 7 days?`
*   **Expected Bot Response:** A message showing the portfolio's performance over the last 7 days, including the current value, past value, absolute change, and percentage change.

---

### 8. Personalized Market Insights

**Test 1: Get Insights**
*   **Your Message:** `/insights` or `Give me market insights`
*   **Expected Bot Response:** A message containing analysis of your holdings, potential market trends, or other relevant insights.

---

### 9. Price Alerts

**Test 1: Set Price Alert**
*   **Your Message:** `Alert me when BTC goes above 115000`
*   **Expected Bot Response:** A confirmation message stating that the alert has been set (e.g., "Alert set: I will notify you if BTC > $115,000"). When the condition is met, you should receive a separate notification.

---

### 10. Portfolio Rebalance

**Test 1: Suggest and Execute Rebalance**
*   **Your Message:** `Rebalance my portfolio to 50% BTC and 50% ETH`
*   **Expected Bot Response:**
    1.  A summary of the proposed swaps to achieve the target allocation.
    2.  A confirmation prompt for the first swap in the plan.
    3.  After confirming each swap, a message indicating the progress (e.g., "Swap 1 of 2 executed successfully").
    4.  A final message confirming that the rebalance is complete.

---

### 11. Price Charts

**Test 1: Generate Price Chart**
*   **Your Message:** `Show me the price chart for BTC over the last 7 days`
*   **Expected Bot Response:** A PNG image of the price chart for BTC over the last 7 days, with a caption.

---

### 12. Testing with DRY_RUN_MODE

**Test 1: Verify Dry Run is Active**
*   **Setup:** Ensure `DRY_RUN_MODE="True"` in your `.env` file.
*   **Your Message:** `Buy 0.1 ETH with USDT`
*   **Expected Bot Response:** After confirming the swap, the final message should explicitly state that the transaction was a simulation. For example: "[DRY RUN] ✅ Swap Simulated Successfully! ... This was a simulation. No real transaction was executed."

**Test 2: Verify Live Mode is Active**
*   **Setup:** Ensure `DRY_RUN_MODE="False"` in your `.env` file.
*   **Your Message:** `Buy 0.1 ETH with USDT`
*   **Expected Bot Response:** After confirming the swap, the final message should indicate a live transaction and include a transaction hash. For example: "[LIVE] ✅ Swap Executed Successfully! ... Transaction Hash: `0x...`"
