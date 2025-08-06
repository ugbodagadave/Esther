# Active Context: Esther

## 1. Current Focus
The current focus is on implementing the on-demand education feature. The `DRY_RUN_MODE` refinement has been completed and is now stable.

## 2. Recent Changes & Decisions
- **`DRY_RUN_MODE` Refinement Complete**: The `DRY_RUN_MODE` feature has been refactored to ensure consistent application across the codebase. The configuration has been centralized in `src/constants.py`, and comprehensive unit and integration tests have been added to verify its behavior. All relevant documentation has been updated.
- **Portfolio Rebalance Feature Complete**: The portfolio rebalance feature has been fully implemented, including the conversational flow for sequential swap execution.
- **Architectural Refactor**: The application has been refactored from a multi-threaded Flask application to a unified `asyncio` event loop using FastAPI. This has resolved the stability issues and created a robust foundation for future development.
- **Deployment Command Update**: The `render.yaml` file has been updated to use `uvicorn` to run the FastAPI application, which is the correct and stable approach for an ASGI application.
- **Portfolio Service Enhancement**: The `suggest_rebalance` function in `PortfolioService` has been enhanced to calculate the `from_amount` in the token's native units, which is a prerequisite for executing rebalance plans.

## 3. Next Steps
1.  **On-Demand Education**: Begin work on an integrated learning module to explain DeFi concepts on the fly.

## 4. Active Learnings & Insights
- Decimal precision is a critical detail in DeFi applications. Hardcoding values is risky; dynamic lookup is essential.
- Deployment environments (like Render) can have subtle differences from local setups. Understanding how WSGI servers like Gunicorn interact with `asyncio` applications is vital for debugging.
- A stable development environment is a prerequisite for productive feature development. It was necessary to pause and fix the deployment before other work could continue.
