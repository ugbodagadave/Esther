# System Patterns: Esther

## 1. High-Level Architecture
Esther will be built using a modular, service-oriented architecture. This pattern promotes separation of concerns, making the system easier to develop, test, and maintain. The core modules will be:

- **Telegram Bot Interface**: The user-facing entry point. It will handle incoming messages and format outgoing responses.
- **NLP Module**: The brain of the operation, powered by Google Gemini. This module will interpret user intent and extract relevant information.
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
- **Command Pattern**: User requests will be encapsulated as command objects. This will allow for flexible handling of different user intents (e.g., `BuyCommand`, `PriceCheckCommand`) and makes it easier to queue or log requests.
- **Strategy Pattern**: The choice between using Gemini Pro and Gemini Flash will be implemented using the Strategy pattern. A context class will decide which model to use based on the complexity of the user's query, allowing for dynamic and efficient allocation of AI resources.
- **Singleton Pattern**: For managing connections to the database and external APIs. This ensures that only one connection instance is created, which is crucial for managing resources efficiently, especially on a resource-constrained platform like Render's free tier.
- **Observer Pattern**: The custom alert system will use this pattern. The market monitoring service will be the "subject," and user alerts will be "observers." When a market condition matches an alert's criteria, the observers are notified, and a message is sent to the user.

## 3. Scalability and Performance Considerations
- **Asynchronous Operations**: All I/O-bound operations, such as API calls to OKX DEX or the database, will be handled asynchronously using Python's `asyncio`. This is critical for ensuring the bot remains responsive to user input while waiting for external services.
- **Caching**: A caching layer (e.g., using Redis or an in-memory cache) will be implemented for frequently requested, non-time-sensitive data (like educational content or user preferences) to reduce API calls and database load.
- **Render Free Tier Constraints**: Given the use of Render's free tier, the system will be designed to be lightweight. This includes:
    - Graceful handling of service restarts or "spin-downs" by persisting important state to the database.
    - Efficient resource management, particularly memory and CPU, to avoid hitting free-tier limits.
    - Prioritizing Gemini Flash for as many tasks as possible to manage costs and reduce the computational load on the backend.
