# Esther: Your AI Crypto Trading Agent

<div align="center">
  <img src="esther-banner.png" alt="Esther AI Trading Agent Banner">
</div>

**Esther** is an AI Agent that lives in your Telegram chat. It makes trading easy and accessible for everyone by integrating with the OKX DEX aggregator, which allows users to swap cryptocurrencies across multiple blockchains and DEXs for the most competitive prices. With Esther, you can trade, get market updates, and manage your crypto portfolio just by having a conversation.

## 🌟 Our Goal
Decentralized Finance (DeFi) can be confusing. Our goal with Esther is to make it simple. Esther is designed to be a helpful and trustworthy guide for both beginners and experienced traders in the world of crypto.

## ✨ What Esther Can Do

### Key Features
-   **Trade with Simple Chat Commands**:
    -   **Check Prices**: "What's the price of ETH?"
    -   **Buy and Sell Tokens**: "Buy 0.1 ETH with USDC" or "Sell 0.5 ETH for USDT".
    -   **Set Smart Orders**: "Set a stop-loss for BTC at 60000" or "Set a take-profit for ETH at 3500".
    -   **Track & Rebalance Portfolio**: `/portfolio` shows live balances + USD value; automated rebalance suggestions coming soon.
-   **Get Smart Insights**: Use the `/insights` command to get personalized advice and analysis on your crypto holdings.
-   **Trade Safely**: Every trade must be confirmed by you, so you never have to worry about accidental transactions.
-   **Stay Updated with Price Alerts**: Set custom alerts for any cryptocurrency (e.g., "/addalert BTC above 70000").
-   **Practice with a Demo Mode**: A "Dry Run" mode lets you practice trading with real market data without using real money.
-   **Manage Your Account**: Esther automatically creates and manages your user profile.
-   **Cross-Chain Swaps**: Swap tokens across different blockchains, like from Ethereum to Polygon, with a single command.
-   **Keep Your Wallet Secure**: You can add, view, and delete your wallet addresses with confidence, as your private keys are always encrypted.
-   **Powered by Advanced AI**: Esther uses Google's Gemini models to understand your commands and provide intelligent responses.
-   **Reliable and Always On**: Esther is deployed on Render, a modern and reliable cloud platform, with a health check to ensure it's always running.

### What's Coming Next
-   **Learn as You Go**: An in-app guide to help you understand DeFi concepts.

## 🛠️ The Technology Behind Esther

-   **Programming Language**: Python
-   **AI and Language Processing**: Google Gemini 2.5 Pro & Flash
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
-   An OKX DEX API Key, Secret, Passphrase **and Project ID** (required for Explorer & Market endpoints)
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
    ```

4.  **Set Up the Database:**
    The app will automatically create the tables it needs when you run it for the first time.

5.  **Start the Bot:**
    ```bash
    python src/main.py
    ```
    This will start the bot, and it will begin listening for your commands in Telegram.

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


## 📄 License

This project is licensed under the MIT License. You can find the full license text in the `LICENSE` file.
