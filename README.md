# Esther: The OKX DEX AI Trading Agent

<div align="center">
  <img src="https://placehold.co/600x300/000000/FFFFFF/png?text=Esther+AI" alt="Esther AI Trading Agent Banner">
</div>

**Esther** is a sophisticated, AI-powered trading agent that operates within Telegram. It provides a seamless, conversational interface to the OKX Decentralized Exchange (DEX), empowering users to trade, analyze the market, and manage their portfolio using natural language.

## 🌟 Core Philosophy
The world of Decentralized Finance (DeFi) is powerful but complex. Esther's mission is to democratize access to DeFi by abstracting away the technical hurdles. It serves as an intelligent, trustworthy, and educational co-pilot for both novice investors and experienced traders.

## ✨ Features

### Current Features
-   **Conversational Trading**:
    -   **Get Live Quotes**: Ask for the price of any token (e.g., "What's the price of ETH?").
    -   **Execute Swaps**: Initiate token swaps with simple commands (e.g., "Buy 0.1 ETH with USDC" or "Sell 0.5 ETH for USDT").
-   **Secure Confirmation Flow**: All transactions require explicit user confirmation via interactive buttons, preventing accidental trades.
-   **Real-time Price Alerts**: Set up custom price alerts for any token (e.g., "/addalert BTC above 70000").
-   **Dry Run Mode**: A global simulation mode that uses live market data to demonstrate trading functionality without executing real on-chain transactions. Perfect for safe testing and demos.
-   **User Account Management**: Automatically creates and manages user profiles in a secure PostgreSQL database.
-   **Secure Wallet Management**: Add, list, and delete your wallet addresses securely. Private keys are encrypted before being stored.
-   **Intelligent Intent Parsing**: Powered by Google's Gemini models (`2.5-pro` and `2.5-flash`) to understand user commands.
-   **Robust Deployment**: Fully configured for continuous deployment on Render, including a Flask health check endpoint to ensure uptime.

### Upcoming Features
-   **Advanced Order Types**: Support for conditional trades and stop-loss/take-profit orders.
-   **Personalized Market Insights**: Proactive trend analysis and portfolio-based recommendations.
-   **On-Demand Education**: An integrated learning module to explain DeFi concepts on the fly.

## 🛠️ Tech Stack

-   **Backend**: Python 3.9+, `asyncio`
-   **AI & NLP**: Google Gemini 2.5 Pro & Flash
-   **Bot Framework**: `python-telegram-bot`
-   **Web Server**: Flask (for Render health checks)
-   **Database**: PostgreSQL
-   **DEX Integration**: OKX DEX API v5
-   **Deployment**: Render

For a detailed technical breakdown, see [How It Works](./how-it-works.md).

## 🚀 Getting Started

### Prerequisites

-   Python 3.9+
-   A Telegram Bot Token
-   A Google Gemini API Key
-   An OKX DEX API Key, Secret, and Passphrase
-   A PostgreSQL database URL (e.g., from Render's free tier)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ugbodagadave/Esther.git
    cd Esther
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory and populate it with your credentials.
    ```dotenv
    # Telegram and AI
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    GEMINI_API_KEY="your_gemini_api_key"

    # OKX API Credentials
    OKX_API_KEY="your_okx_api_key"
    OKX_API_SECRET="your_okx_api_secret"
    OKX_API_PASSPHRASE="your_okx_api_passphrase"

    # Database
    DATABASE_URL="your_postgresql_connection_string"
    
    # A test wallet address for development
    TEST_WALLET_ADDRESS="your_ethereum_test_wallet_address"
    ```

4.  **Initialize the database:**
    The application will automatically create the necessary `users` table on startup if it doesn't exist.

5.  **Run the bot:**
    ```bash
    python src/main.py
    ```
    This will start the bot in polling mode and run the Flask web server in a background thread to handle health checks.

## ⚙️ Configuration

### Dry Run Mode
For safe testing and development, the bot includes a `DRY_RUN_MODE`. When enabled, all swap transactions are simulated using live market data, but no real on-chain transactions are executed. This is the default behavior.

To enable or disable Dry Run Mode, set the `DRY_RUN_MODE` variable in your `.env` file:
```dotenv
# Set to "True" to simulate all transactions (default and recommended for testing)
DRY_RUN_MODE="True"

# Set to "False" to execute real transactions on the blockchain
# DRY_RUN_MODE="False"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss proposed changes.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
