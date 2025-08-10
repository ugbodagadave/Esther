# System Patterns: Esther

## 1. High-Level Architecture
Esther is built using a modular, service-oriented architecture. This pattern promotes separation of concerns, making the system easier to develop, test, and maintain. The core modules are:

- **Telegram Bot Interface**: The user-facing entry point. It handles incoming messages and formats outgoing responses.
- **NLP Module**: The brain of the operation, powered by Google Gemini. This module interprets user intent and extracts relevant information.
- **Core Logic/Business Layer**: Orchestrates the interactions between the NLP module, the DEX API, and the database. It contains the primary business logic of the application.
- **Data Access Layer**: Manages all interactions with the database, abstracting the database logic from the core application.
- **External Services Layer**: Handles all communication with third-party APIs (OKX DEX, News APIs, etc.).

```mermaid
graph TD
    A[Telegram User] -->|Sends Command| B(Telegram Bot Interface)
    B -->|User Input| C{NLP Module (Gemini)}
    C -->|Parsed Intent| D[Core Logic Layer]
    D -->|DB Queries| F(Data Access Layer)
    F -->|User/App Data| E[Database]
    D -->|API Calls| G(External Services Layer)
    G -->|Market/News Data| H[OKX DEX & Other APIs]
    D -->|Response Data| B
    B -->|Sends Message| A
```

## 2. Key Design Patterns
- **Command Pattern**: User requests are encapsulated as command objects. This allows for flexible handling of different user intents (e.g., `BuyCommand`, `PriceCheckCommand`) and makes it easier to queue or log requests.
- **Strategy Pattern**: The choice between using Gemini Pro and Gemini Flash is implemented using the Strategy pattern. A context class decides which model to use based on the complexity of the user's query, allowing for dynamic and efficient allocation of AI resources.
- **Singleton Pattern**: For managing connections to the database and external APIs. This ensures that only one connection instance is created, which is crucial for managing resources efficiently.
- **Observer Pattern**: The custom alert system uses this pattern. The market monitoring service is the "subject," and user alerts are "observers." When a market condition matches an alert's criteria, the observers are notified, and a message is sent to the user.
- **Custom Exceptions**: The application uses a set of custom exception classes to handle specific error conditions gracefully. This allows for more granular error handling and user-friendly error messages.

## 3. Deployment Strategy
- **Development (Current)**: The application runs in a **polling mode** using a simple `python src/main.py` command. This is a stable, single-process method ideal for development and debugging on Render's free tier.
- **Production (Future)**: The system is designed to be deployed using a **webhook model** with a WSGI server like Gunicorn. This is a more scalable and efficient architecture suitable for handling higher traffic. The `main.py` script includes a Flask application to handle incoming webhook requests from Telegram.

## 4. Scalability and Performance Considerations
- **Asynchronous Operations**: All I/O-bound operations, such as API calls to OKX DEX or the database, are handled asynchronously using Python's `asyncio`. This is critical for ensuring the bot remains responsive.
- **Caching**: A caching layer will be implemented for frequently requested data to reduce API calls and database load.
- **Render Free Tier Constraints**: The system is designed to be lightweight to operate within the limits of Render's free tier. This includes efficient resource management and prioritizing Gemini Flash for simpler tasks.

## 5. Conversation & Validation Patterns
- **Validation-First Confirmation**: Before executing a swap, validate user settings that affect safety (e.g., live trading enabled requires a default wallet) even if environment is in simulation mode.
- **Lazy Initialization**: Services created during app startup (e.g., `TokenResolver`) should be lazily checked/instantiated in handlers to prevent test/startup race conditions.
- **Symbol Normalization**: Normalize symbols that differ between instrument and token contexts (e.g., `BTC`→`WBTC` for EVM swaps; `BTC-USD` for market candles) in a single resolver to keep business logic consistent.
- **Human-Readable Help Menu**: Present capabilities as bullets with em dashes, no code backticks, optimized for quick scanning.
- **Mobile WebApp Fallback**: Prefer inline WebApp buttons, with an optional reply-keyboard WebApp fallback behind `MOBILE_WEBAPP_FALLBACK` for Android clients that require it.
