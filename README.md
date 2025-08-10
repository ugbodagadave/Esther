# Esther: Your AI Crypto Trading Agent

<div align="center">
  <img src="esther-banner.png" alt="Esther AI Trading Agent Banner">
</div>

**Esther** is an AI Agent that lives in your Telegram chat. It makes trading easy and accessible for everyone by integrating with the **OKX DEX API**, which allows users to swap cryptocurrencies across multiple blockchains and DEXs for the most competitive prices. With Esther, you can trade, get market updates, and manage your crypto portfolio just by having a natural conversation.

This project is submitted for the **OKX ETHCC Hackathon**, in the **DeFi, RWAs & Autonomous Apps** track.

## ✨ Core Functionalities

Esther is designed to be a comprehensive AI trading assistant. Here are its core functionalities and the endpoints that power them:

| Functionality | Description | OKX DEX API Endpoint(s) |
| :--- | :--- | :--- |
| **Live Price Quotes** | Get real-time price quotes for any token pair. | `/api/v5/dex/aggregator/quote` |
| **Token Swaps** | Execute trades across multiple DEXs to get the best price. | `/api/v5/dex/aggregator/swap` |
| **Portfolio Tracking** | Get a real-time snapshot of your wallet balances and their USD value. | `/api/v5/dex/balance/all-token-balances-by-address` |
| **Price Alerts** | Set custom price alerts to get notified of market movements. | `/api/v5/dex/aggregator/quote` |
| **Portfolio Rebalancing**| Automatically generate and execute a plan to rebalance your portfolio. | `/api/v5/dex/aggregator/swap` |
| **Portfolio Performance**| Track the historical performance of your crypto assets. | `/api/v5/dex/historical-index-price` |
| **Price Charts**| Generate a price chart for a token over a specified period. | `/api/v5/market/history-candles`, `/api/v5/wallet/token/historical-price` |
| **Token Resolution**| Dynamically resolve token metadata to ensure accurate pricing. | (Internal) |

For a detailed explanation of how we integrated the OKX DEX API, see our [OKX DEX API Integration Guide](./okx_dex_api_integration.md).

For a more detailed breakdown of how these features work, please see the [How It Works](./how-it-works.md) guide.

## 🛠️ The Technology Behind Esther

-   **Programming Language**: Python
-   **AI and Language Processing**: Google Gemini 2.5 Pro & Flash
-   **Bot Framework**: `python-telegram-bot`
-   **Web Server**: FastAPI
-   **Database**: PostgreSQL
-   **Crypto Exchange**: **OKX DEX API**
-   **Cloud Hosting**: Render
-   **L2 Focus**: OKX X Layer (zkEVM, Polygon CDK, OKB gas)

## 🚀 How to Get Started

### What You'll Need

-   Python (version 3.9 or higher)
-   A Telegram Bot Token
-   A Google Gemini API Key
-   An OKX DEX API Key, Secret, Passphrase **and Project ID**
-   A PostgreSQL database URL

### Step-by-Step Setup

1.  **Download the Code:**
    ```bash
    git clone https://github.com/ugbodagadave/Esther.git
    cd Esther
    ```

2.  **Set Up Your Workspace and Install Dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Add Your Secret Keys:**
    Create a file named `.env` in the main folder and add your secret keys:
    ```dotenv
    # Core
    TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
    GEMINI_API_KEY="your_gemini_api_key"
    DATABASE_URL="your_postgresql_connection_string"
    ENCRYPTION_KEY="your_32_byte_base64_fernet_key"

    # OKX DEX API
    OKX_API_KEY="your_okx_api_key"
    OKX_API_SECRET="your_okx_api_secret"
    OKX_API_PASSPHRASE="your_okx_api_passphrase"
    OKX_PROJECT_ID="your_okx_project_id"  # injected as OK-ACCESS-PROJECT

    # Webhook / Hosting
    WEBHOOK_URL="https://your-public-domain"  # Render URL; if unset, bot uses polling

    # Behavior
    DRY_RUN_MODE="True"  # default simulation mode

    # Monitoring (optional)
    PORTFOLIO_SYNC_INTERVAL="600"       # seconds (default: 600)
    ALERT_QUOTE_DELAY_MS="100"          # default 100
    ALERT_ERROR_BACKOFF_MS="500"        # default 500

    # Mobile Web App fallback (optional)
    MOBILE_WEBAPP_FALLBACK="False"  # set True to also send a reply-keyboard WebApp button on mobile

    # Admin (optional but recommended for dev tools)
    ADMIN_SECRET_KEY="a_long_random_string"

    # Error Handling (optional)
    ERROR_ADVISOR_ENABLED="False"       # set True to enable LLM FailureAdvisor on error paths

    # Handler timeouts (optional)
    HANDLER_TIMEOUT_SECS="180"          # per-step watchdog timeout in seconds

    # Circuit Breaker (optional)
    CIRCUIT_FAIL_THRESHOLD="5"          # consecutive failures to open breaker
    CIRCUIT_RESET_SECS="30"             # cooldown before half-open trial

    # Backoff Tuning (optional)
    BACKOFF_BASE_SECS="0.2"
    BACKOFF_MULTIPLIER="2.0"
    BACKOFF_MAX_SECS="5.0"
    BACKOFF_JITTER_FRAC="0.1"
    ```

4.  **Start the Bot:**
    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 8080
    ```

## 🧪 Testing

To ensure all functionalities are working correctly, you can refer to the [**TESTING_GUIDE.md**](./TESTING_GUIDE.md). This guide provides a comprehensive set of natural language prompts to test all of Esther's features, from basic price checks to complex portfolio rebalancing.

## 💡 Potential for X Layer Integration

- X Layer is OKX’s zkEVM Layer‑2 built with Polygon CDK, using **OKB** as the gas token and offering full EVM compatibility with low fees and fast finality.
- Esther can target X Layer by supplying its chain identifier to existing OKX Aggregator quote/swap calls and including it in portfolio balance sync—no contract rewrites required.
- For first‑time users, the bot can deep‑link to OKX Bridge to fund X Layer quickly.

See the concise plan in `okx_dex_api_integration.md`.

## ⚙️ Live Trading vs Dry Run

- By default, Esther runs in simulation mode controlled by the `DRY_RUN_MODE` environment variable (default: `True`).
- To execute real swaps:
  - Set `DRY_RUN_MODE="False"` in `.env`.
  - Enable live trading in-chat via `/enablelivetrading`.
  - Set a default wallet via `/setdefaultwallet`.
- When live trading is enabled but `DRY_RUN_MODE` remains `True`, swaps are still simulated; however, the bot validates that a default wallet exists in your account. If missing or not found, the operation aborts with a clear message.

Esther includes a robust, phased error handling system for clear guidance during failures. See `error_handling.md` for details.

## 🙏 Acknowledgements

We would like to extend our sincere gratitude to **OKX** for providing the powerful and versatile DEX API that serves as the backbone of this project. The comprehensive features and robust performance of the OKX DEX API have been instrumental in bringing Esther to life.
