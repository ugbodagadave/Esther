# Technical Context: Esther

## 1. Core Technologies
- **Programming Language**: Python will be the primary language for development due to its robust ecosystem of libraries for AI, web development, and API integration, which is ideal for this project.
- **AI Models**:
    - **Google Gemini 2.5 Pro**: The core engine for complex NLP tasks, including parsing trading commands, market analysis, personalized recommendations, and sentiment analysis.
    - **Google Gemini 2.5 Flash**: Used for high-volume, low-latency tasks such as answering simple queries, handling basic conversation, and initial intent recognition.
- **Primary Interface**: The **Telegram Bot API** will be used to manage all user interactions within the Telegram platform.
- **Database**: **PostgreSQL** will be used as the relational database. It provides a robust and scalable solution for storing user data, trade history, and configurations. The database will be hosted on Render's free tier.

## 2. Core Integrations
- **OKX DEX API**: This is the central integration for all trading-related functionality. It will be used to fetch market data, execute trades, and manage user portfolios. Secure and efficient interaction with this API is a top priority.
- **News APIs**: Integration with a reliable crypto news source like **NewsAPI** or **CryptoCompare API** is required to power the news aggregation and sentiment analysis features.
- **Blockchain Explorers**: APIs from services like **Etherscan** (for Ethereum) and **Solscan** (for Solana) will be used to verify transaction statuses, fetch real-time gas fees, and gather other on-chain data.

## 3. Development & Deployment
- **Development Environment**: The project will be developed using standard Python tools, including a virtual environment (`venv`) and a `requirements.txt` file for managing dependencies.
- **Version Control**: **Git** will be used for version control, with the repository hosted on GitHub.
- **Deployment**: For the initial development and testing phases, the application will be deployed on **Render**. This provides a simple and cost-effective platform for hosting the bot and its backend services. For a full production environment, a more robust cloud provider like AWS or GCP will be considered.

## 4. Security & API Key Management
- All sensitive credentials, including Telegram Bot Tokens, OKX DEX API keys, and Gemini API keys, will be managed securely using environment variables.
- User-specific API keys or wallet information stored in the database will be encrypted to prevent unauthorized access.
