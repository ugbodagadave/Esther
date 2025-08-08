# Active Context: Esther

## 1. Current Focus
The current focus is on planning the implementation of the new "Simple Price Charts" feature.

## 2. Recent Changes & Decisions
- **Portfolio Performance Bug Fix**: Fixed a critical bug in the `portfolio_performance` function where the time period was not being correctly parsed from user input. The new implementation is more robust and handles a wider variety of user inputs (e.g., "14 days", "28d", "last month").
- **Portfolio Performance Tracker**: Implemented the core feature, including database schema changes, new API client methods, and the conversational flow.
- **Error Handling**: Implemented a robust error handling system for the wallet addition feature. This includes creating custom exceptions, refactoring the database and main application logic to handle these exceptions gracefully, and adding comprehensive unit tests to ensure the new system works as expected.
- **UI Improvements**: The UI of the secure wallet input web app has been updated to a dark-themed, neo-brutalism design.
- **Concurrency Fix**: Resolved a critical bug that caused the bot to process messages twice by removing the redundant polling loop when a webhook is active.
- **Secure Wallet Input**: Implemented a secure web app for private key entry, enhancing security by preventing sensitive data from being stored in chat history.
- **`DRY_RUN_MODE` Refinement Complete**: The `DRY_RUN_MODE` feature has been refactored to ensure consistent application across the codebase. The configuration has been centralized in `src/constants.py`, and comprehensive unit and integration tests have been added to verify its behavior. All relevant documentation has been updated.
- **Portfolio Rebalance Feature Complete**: The portfolio rebalance feature has been fully implemented, including the conversational flow for sequential swap execution.
- **Architectural Refactor**: The application has been refactored from a multi-threaded Flask application to a unified `asyncio` event loop using FastAPI. This has resolved the stability issues and created a robust foundation for future development.
- **Deployment Command Update**: The `render.yaml` file has been updated to use `uvicorn` to run the FastAPI application, which is the correct and stable approach for an ASGI application.
- **Portfolio Service Enhancement**: The `suggest_rebalance` function in `PortfolioService` has been enhanced to calculate the `from_amount` in the token's native units, which is a prerequisite for executing rebalance plans.

## 3. Next Steps
1.  **Implement Simple Price Charts**: Begin work on the new feature to allow users to request and view simple price charts for a given token and time period.
2.  **On-Demand Education**: Begin work on an integrated learning module to explain DeFi concepts on the fly.

## 4. Active Learnings & Insights
- Robust input parsing is crucial for a good user experience. A simple regex or string matching is often not enough to handle the variety of user inputs.
- Decimal precision is a critical detail in DeFi applications. Hardcoding values is risky; dynamic lookup is essential.
- Deployment environments (like Render) can have subtle differences from local setups. Understanding how WSGI servers like Gunicorn interact with `asyncio` applications is vital for debugging.
- A stable development environment is a prerequisite for productive feature development. It was necessary to pause and fix the deployment before other work could continue.
