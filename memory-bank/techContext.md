# Technical Context: Esther

## 1. Core Technologies
- **Programming Language**: Python is the primary language for development due to its robust ecosystem of libraries for AI, web development, and API integration.
- **AI Models**:
    - **Google Gemini 2.5 Pro**: The core engine for complex NLP tasks, including parsing trading commands, market analysis, and personalized recommendations.
    - **Google Gemini 2.5 Flash**: Used for high-volume, low-latency tasks such as answering simple queries and initial intent recognition.
- **Primary Interface**: The **Telegram Bot API** is used to manage all user interactions.
- **Database**: **PostgreSQL** is used as the relational database, hosted on Render's free tier.

## 2. Core Integrations
- **OKX DEX API**: This is the central integration for all trading-related functionality. It is used to fetch market data, execute trades, and manage user portfolios.
- **News APIs**: Integration with a reliable crypto news source like **NewsAPI** or **CryptoCompare API** is required to power news aggregation and sentiment analysis.
- **Blockchain Explorers**: APIs from services like **Etherscan** will be used to verify transaction statuses and fetch other on-chain data.

## 3. Development & Deployment
- **Development Environment**: Standard Python tools, including `venv` and `requirements.txt`, are used for managing dependencies.
- **Version Control**: **Git** is used for version control, with the repository hosted on GitHub.
- **Deployment**:
    - **Current (Development)**: The application is deployed on **Render** using a stable **polling** mechanism (`python src/main.py`). This is ideal for the current development and debugging phase.
    - **Future (Production)**: The application is designed to be deployed using a **webhook** model with a WSGI server like **Gunicorn**, which is more scalable for production environments.

## 4. Security & API Key Management
- All sensitive credentials, including Telegram Bot Tokens, OKX DEX API keys, and Gemini API keys, are managed securely using environment variables.
- User-specific API keys or wallet information stored in the database are encrypted to prevent unauthorized access.

## 5. Trading Flow Technical Notes
- `confirm_swap` determines live vs simulation using two flags: per-user `live_trading_enabled` and global `DRY_RUN_MODE`.
- If user enabled live trading:
  - Default wallet must exist; absence aborts the flow with a clear message (even in simulation).
  - For live trades (`DRY_RUN_MODE` = False), the default wallet’s encrypted private key is decrypted in-memory for signing.
- `TokenResolver` is lazily instantiated inside `confirm_swap` to avoid NoneType issues when handlers are invoked without full app startup.
