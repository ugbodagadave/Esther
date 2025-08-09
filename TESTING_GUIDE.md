# Esther Bot Testing Guide

Here is a concise guide to testing Esther’s features using natural language prompts. It reflects the updated friendly tone, help menu, and secure wallet flow.

---

### 0. After Clearing the Database (development)
- If you use the admin clear‑DB tool, restart the app, or if the first `/start` shows an account access error, send `/start` once more so Esther can re‑initialize the schema automatically.

---

### 1. Basic Interaction

**Test 1: Start Command**
- Your Message: `/start`
- Expected Bot Response: A warm welcome such as: "Hello! I'm Esther — your friendly DeFi co‑pilot. Ready when you are! 🚀"

**Test 2: Help Command**
- Your Message: `/help`
- Expected Bot Response: A capability list covering:
  - Portfolio & performance (snapshot, performance window, price charts)
  - Wallets (add via secure Web App, list, delete, set default)
  - Trading & quotes (buy/sell; quick price checks)
  - Alerts (set, list)
  - Insights & rebalance
  - Live trading controls (enable/disable)

---

### 2. Price Checks

**Test 1: Price of BTC**
- Your Message: `What's the price of BTC?`
- Expected Bot Response: Current price estimate.

**Test 2: Price of ETH**
- Your Message: `How much is ETH worth?`
- Expected Bot Response: Current price estimate.

**Test 3: Unsupported token**
- Your Message: `What's the price of FOO?`
- Expected Bot Response: A polite "not supported" reply.

---

### 3. Wallet Management

**Test 1: Show Wallets**
- Your Message: `Show me my wallets`
- Expected: A list of saved wallets or a hint to add one.

**Test 2: Add a New Wallet (secure Web App)**
- Your Message: `I want to add a new wallet`
- Expected: Conversation asks for name and address, then shows a button "Enter Private Key Securely" to open the Web App. After submission, confirmation: `✅ Wallet '<name>' added successfully!`

**Test 3: Set Default Wallet**
- Your Message: `/setdefaultwallet`
- Expected: Inline choices; confirm selection.

**Test 4: Enable Live Trading**
- Your Message: `/enablelivetrading`
- Expected: Shows current status with Enable/Disable buttons; confirmation upon change.

---

### 4. Trading (Buy, Sell, Swap)

Notes:
- When `DRY_RUN_MODE="True"`, swaps simulate. If live trading is enabled, the bot still validates that a default wallet exists; otherwise it aborts with a clear message.

Examples:
- `Buy 0.1 ETH with USDC`
- `Sell 50 USDC for ETH`

---

### 5. Cross‑Chain & Network Targeting

- Optional exploratory prompt (future‑facing UX): `Buy 10 OKB on X Layer`
- Current implementation remains chain‑id based via OKX Aggregator; explicit X Layer support can be added by mapping the network name to the proper chain parameter.

---

### 6. Advanced Orders

**Test 1: Set Stop Loss**
- Your Message: `Set a stop loss for BTC at 110000`
- Expected: Confirmation message.

**Test 2: Set Take Profit**
- Your Message: `Set a take profit for ETH at 3700`
- Expected: Confirmation message.

---

### 7. Portfolio Tracking

**Test 1: Show Portfolio**
- Your Message: `/portfolio`
- Expected: A formatted table of holdings and USD value.

**Test 2: Portfolio Performance**
- Your Message: `How has my portfolio performed over the last 7 days?`
- Expected: Current value, past value, absolute and percentage change.

---

### 8. Personalized Market Insights

**Test 1: Get Insights**
- Your Message: `/insights` or `Give me market insights`
- Expected: Friendly, concise insights using your real snapshot, with a brief non‑advice reminder.

---

### 9. Price Alerts

**Test 1: Set Price Alert**
- Your Message: `Alert me when BTC goes above 115000`
- Expected: `✅ Alert set!` plus condition text.
- Notes: Background worker applies light throttling and backoff. Tunables:
  - `ALERT_QUOTE_DELAY_MS` (default 100)
  - `ALERT_ERROR_BACKOFF_MS` (default 500)

**Test 2: List Alerts**
- Your Message: `/listalerts`
- Expected: Active alerts displayed.

---

### 10. Portfolio Rebalance

**Test 1: Suggest and Execute Rebalance**
- Your Message: `Rebalance my portfolio to 50% BTC and 50% ETH`
- Expected:
  1) Summary of proposed swaps
  2) Confirmation for the first swap
  3) Progress messages per swap
  4) Final completion message

---

### 11. Price Charts

**Test 1: Generate Price Chart**
- Your Message: `Show me the price chart for BTC over the last 7 days`
- Expected: A PNG image with a caption like `Price chart for BTC (7d)`.

---

### 12. DRY_RUN_MODE Behavior
- When `DRY_RUN_MODE="True"` and live trading is enabled, a valid default wallet is still required; otherwise the confirmation flow aborts with a clear message instead of simulating.
