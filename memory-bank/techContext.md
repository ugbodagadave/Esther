# Technical Context: Esther

## 1. Core Technologies
- **Programming Language**: Python is the primary language for development due to its robust ecosystem of libraries for AI, web development, and API integration.
- **AI Models**:
    - **Google Gemini 2.5 Pro**: The core engine for complex NLP tasks, including parsing trading commands, market analysis, and personalized recommendations.
    - **Google Gemini 2.5 Flash**: Used for high-volume, low-latency tasks such as answering simple queries and initial intent recognition.
- **Primary Interface**: The **Telegram Bot API** is used to manage all user interactions.
- **Database**: **PostgreSQL** is used as the relational database, hosted on Render's free tier.

## 2. Core Integrations
- **OKX DEX API**: Central integration for quotes/swaps/portfolio.
- **OKX X Layer**: zkEVM L2 (Polygon CDK, OKB gas). Esther can target X Layer by passing its chain identifier to OKX Aggregator; portfolio sync includes X Layer addresses. No contract rewrites needed (EVM compatible).
- **News APIs**: Integration with a reliable crypto news source like **NewsAPI** or **CryptoCompare API** is required to power news aggregation and sentiment analysis.
- **Blockchain Explorers**: APIs from services like **Etherscan** will be used to verify transaction statuses and fetch other on-chain data.

## 3. Development & Deployment
- Render hosting; webhook via `WEBHOOK_URL` when set, otherwise polling.
- Telegram Web App (private key input) served at `/web-app/index.html`.
- Android inline WebApp requires BotFather `/setdomain` configured with the HTTPS origin.

## 4. Security & API Key Management
- Environment variables (subset): `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `DATABASE_URL`, `ENCRYPTION_KEY`, `OKX_API_KEY`, `OKX_API_SECRET`, `OKX_API_PASSPHRASE`, `OKX_PROJECT_ID`, `WEBHOOK_URL`, `DRY_RUN_MODE`, optional `TEST_WALLET_ADDRESS`, `TEST_WALLET_PRIVATE_KEY`, `PORTFOLIO_SYNC_INTERVAL`, `ALERT_QUOTE_DELAY_MS`, `ALERT_ERROR_BACKOFF_MS`, `MOBILE_WEBAPP_FALLBACK`, `ADMIN_SECRET_KEY`.
- User-specific API keys or wallet information stored in the database are encrypted to prevent unauthorized access.

## 5. Trading Flow Technical Notes
- `confirm_swap` determines live vs simulation using two flags: per-user `live_trading_enabled` and global `DRY_RUN_MODE`.
- If user enabled live trading:
  - Default wallet must exist; absence aborts the flow with a clear message (even in simulation).
  - For live trades (`DRY_RUN_MODE` = False), the default wallet’s encrypted private key is decrypted in-memory for signing.
- `TokenResolver` is lazily instantiated inside `confirm_swap` to avoid NoneType issues when handlers are invoked without full app startup.
- BTC Handling: For EVM address contexts (quotes/swaps), `BTC` is aliased to `WBTC` for address/decimals; for charts, `BTC` uses the `BTC-USD` instrument ID.

## 6. Monitoring Backoff & Throttling (A4)
- Alert checks use a small per-alert delay with jitter to avoid bursts.
- On quote errors or suspected rate limiting, the worker backs off briefly before continuing.
- Environment variables:
  - `ALERT_QUOTE_DELAY_MS` (default 100)
  - `ALERT_ERROR_BACKOFF_MS` (default 500)

## 7. Insights Data Source (A5)
- Insights now consume `PortfolioService.get_snapshot()` to build holdings `{symbol: quantity}`.
- Minimal enrichment from OKX DEX quote endpoints is included in the prompt context.
