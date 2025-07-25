# Esther: The OKX DEX AI Trading Agent

 <!-- Placeholder for a project banner -->

Esther is a sophisticated, AI-powered trading agent that operates within Telegram. It provides a conversational interface to the OKX Decentralized Exchange (DEX), allowing users to trade, analyze the market, and manage their portfolio using natural language.

## ✨ Features

-   **Natural Language Trading**: Execute trades, swaps, and complex conditional orders on OKX DEX using plain English.
-   **Intelligent Market Analysis**: Get real-time market data, trend analysis, and predictive insights powered by Google Gemini.
-   **Personalized Recommendations**: Receive tailored trading strategies and portfolio advice based on your trading history and risk profile.
-   **On-Demand Education**: Learn about DeFi concepts, trading mechanics, and blockchain technology through a conversational interface.
-   **Portfolio Management**: Track your asset performance, analyze diversification, and get suggestions for rebalancing.
-   **Custom Alerts**: Set up highly customizable alerts for price movements, volume changes, and more.

## 🛠️ Tech Stack

-   **Backend**: Python, `asyncio`
-   **AI**: Google Gemini Pro & Flash
-   **Platform**: Telegram
-   **Database**: MongoDB
-   **DEX Integration**: OKX DEX API
-   **Deployment**: Render

## 🚀 Getting Started

### Prerequisites

-   Python 3.9+
-   A Telegram Bot Token
-   A Google Gemini API Key
-   An OKX DEX API Key
-   A NewsAPI.org API Key
-   A MongoDB instance

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
    Create a `.env` file in the root directory and add the following:
    ```
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    GEMINI_API_KEY=your_gemini_api_key
    OKX_API_KEY=your_okx_api_key
    OKX_API_SECRET=your_okx_api_secret
    OKX_API_PASSPHRASE=your_okx_api_passphrase
    NEWS_API_KEY=your_news_api_key
    MONGO_DB_URI=your_mongodb_uri
    ENCRYPTION_KEY=a_secure_random_32_byte_string
    ```

4.  **Run the bot:**
    ```bash
    python main.py
    ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
