# Esther: Your AI Crypto Trading Agent

<div align="center">
  <img src="esther-banner.png" alt="Esther AI Trading Agent Banner">
</div>

**Esther** is an AI Agent that lives in your Telegram chat. It makes trading easy and accessible for everyone by integrating with the OKX DEX aggregator, which allows users to swap cryptocurrencies across multiple blockchains and DEXs for the most competitive prices. With Esther, you can trade, get market updates, and manage your crypto portfolio just by having a natural conversation.

## 🌟 Our Goal
Decentralized Finance (DeFi) can be confusing. Our goal with Esther is to make it simple. Esther is designed to be a helpful and trustworthy guide for both beginners and experienced traders in the world of crypto.

## ✨ What Esther Can Do

### Key Features
-   **Trade with Natural Language**:
    -   **Check Prices**: "What's the price of ETH?" or "How much is Bitcoin worth?"
    -   **Buy and Sell Tokens**: "Buy 0.1 ETH with USDC" or "I want to sell some Bitcoin for USDT".
    -   **Set Smart Orders**: "Set a stop-loss for BTC at 60000" or "Alert me when ETH reaches 3500".
    -   **Track & Rebalance Portfolio**: "Show me my portfolio" or "What's in my wallet?" displays live balances + USD value; automated rebalance suggestions coming soon.
-   **Manage Your Wallets**: "Show me my wallets" or "I want to add a new wallet" - manage your wallet addresses securely with encrypted private keys.
-   **Get Smart Insights**: "Give me market insights" or "What's the market analysis?" - get personalized advice and analysis on your crypto holdings.
-   **Trade Safely**: Every trade must be confirmed by you, so you never have to worry about accidental transactions.
-   **Stay Updated with Price Alerts**: Set custom alerts for any cryptocurrency (e.g., "Alert me if BTC goes above 70000").
-   **Practice with a Demo Mode**: A "Dry Run" mode lets you practice trading with real market data without using real money.
-   **Manage Your Account**: Esther automatically creates and manages your user profile.
-   **Cross-Chain Swaps**: Swap tokens across different blockchains, like from Ethereum to Polygon, with a single command.
-   **Powered by Advanced AI**: Esther uses Google's Gemini 2.5 Pro & Flash models to understand your natural language commands and provide intelligent responses.
-   **Reliable and Always On**: Esther is deployed on Render, a modern and reliable cloud platform, with a health check to ensure it's always running.

### What's Coming Next
-   **Learn as You Go**: An in-app guide to help you understand DeFi concepts.

## 🛠️ The Technology Behind Esther

-   **Programming Language**: Python
-   **AI and Language Processing**: Google Gemini 2.5 Pro & Flash (Intelligent Model Selection)
-   **Bot Framework**: `python-telegram-bot`
-   **Web Server**: Flask
-   **Database**: PostgreSQL
-   **Crypto Exchange**: OKX DEX API
-   **Cloud Hosting**: Render

For a more technical look at how Esther works, check out our [How It Works](./how-it-works.md) guide.

For a detailed explanation of how we integrated the OKX DEX API, see our [OKX DEX API Integration Guide](./okx_dex_api_integration.md).

## 🚀 How to Get Started

### What You'll Need

-   Python (version 3.9 or higher)
-   A Telegram Bot Token
-   A Google Gemini API Key
-   An OKX DEX API Key, Secret, Passphrase **and Project ID** (required for DEX portfolio and market data endpoints)
-   A PostgreSQL database URL (you can get one for free from Render)

### Step-by-Step Setup

1.  **Download the Code:**
    ```bash
    git clone https://github.com/ugbodagadave/Esther.git
    cd Esther
    ```

2.  **Set Up Your Workspace and Install a Few Things:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Add Your Secret Keys:**
    Create a file named `.env` in the main folder and add your secret keys, like this:
    ```dotenv
    # For Telegram and the AI
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    GEMINI_API_KEY="your_gemini_api_key"

    # For the OKX Crypto Exchange
    OKX_API_KEY="your_okx_api_key"
    OKX_API_SECRET="your_okx_api_secret"
    OKX_API_PASSPHRASE="your_okx_api_passphrase"
    # The Project ID that groups your keys and quota in OKX Web3 – required for portfolio features
    OKX_PROJECT_ID="your_okx_project_id"

    # For the Database
    DATABASE_URL="your_postgresql_connection_string"
    
    # A test wallet for practice
    TEST_WALLET_ADDRESS="your_ethereum_test_wallet_address"
    TEST_WALLET_PRIVATE_KEY="your_ethereum_test_wallet_private_key"
    ADMIN_SECRET_KEY="your_admin_secret_key"
    ```

4.  **Set Up the Database:**
    The app will automatically create the tables it needs when you run it for the first time.

5.  **Start the Bot:**
    ```bash
    python src/main.py
    ```
    This will start the bot, and it will begin listening for your commands in Telegram.

## 💬 Conversational Features

Esther understands natural language, so you can interact with it just like talking to a friend:

### Example Conversations
- **"Hello Esther!"** → Esther introduces herself and asks what you'd like to do
- **"What's the price of Bitcoin?"** → Gets current BTC price
- **"I want to buy some Ethereum"** → Starts the wallet addition process
- **"Show me my portfolio"** → Displays your current holdings and values
- **"Give me market insights"** → Provides personalized market analysis
- **"What can you do?"** → Lists all available features

### Intelligent Model Selection
Esther automatically chooses the best AI model for your request:
- **Gemini 2.5 Flash**: Fast responses for simple queries and basic tasks
- **Gemini 2.5 Pro**: Deep analysis for complex trading decisions and insights

## ⚙️ Settings

### Demo Mode ("Dry Run")
For safe practice, Esther has a "Dry Run" mode. When it's on, you can simulate trades with real market data without spending any real money. This is the default setting.

To turn demo mode on or off, change the `DRY_RUN_MODE` setting in your `.env` file:
```dotenv
# Set to "True" to practice without real money (this is the default)
DRY_RUN_MODE="True"

# Set to "False" to make real trades on the crypto exchange
# DRY_RUN_MODE="False"
```

### Admin Secret Key
This key is used to protect the new admin endpoint for clearing the database during development.

## 📄 License

This project is licensed under the MIT License. You can find the full license text in the `LICENSE` file.

## Temporary Admin Tools (For Development)
During development, you may need to clear the PostgreSQL database to reset all users, wallets, and portfolio data. A temporary, secure admin page has been added for this purpose.

To clear the database:
1.  Ensure you have set the `ADMIN_SECRET_KEY` environment variable in your `.env` file or in your Render dashboard. This should be a long, random string.
2.  Visit the following URL in your browser:
    `https://esther-bot.onrender.com/admin/clear-db-page/<your_secret_key>`
    
    Replace `<your_secret_key>` with the secret key you set.
3.  Click the "Clear Database Now" button on the page to confirm the action.

### Running the End-to-End Test
The `e2e_test.py` script is provided to perform live checks against the Gemini and OKX APIs.
It requires the following environment variables to be set:

- `GEMINI_API_KEY`
- `OKX_API_KEY`
- `OKX_API_SECRET`
- `OKX_API_PASSPHRASE`
- `OKX_PROJECT_ID`
- `TEST_WALLET_ADDRESS`
- `TEST_WALLET_PRIVATE_KEY`

Run the test with:
```bash
python e2e_test.py
```

This will test all major functionality including conversational NLP, portfolio management, and API integrations.
