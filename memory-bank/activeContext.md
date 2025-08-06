# Active Context: Esther

## 1. Current Focus
The current focus is on stabilizing the development environment and fixing critical bugs. The immediate priority is ensuring core features like price checks are reliable before moving on to new feature development.

## 2. Recent Changes & Decisions
- **Deployment Strategy Shift**: Temporarily switched from a Gunicorn/webhook deployment to a simpler `python src/main.py` polling method on Render to resolve critical `Application not initialized` and `asyncio` event loop errors. This provides a stable development environment.
- **Decimal Precision Bug Fixed**: Resolved a major bug in the `get_price_intent` function where a hardcoded decimal value (18) was causing OKX API errors for tokens with different precisions (like WBTC with 8). Implemented a `TOKEN_DECIMALS` dictionary to dynamically provide the correct precision for API calls.
- **Telegram API Conflict Resolved (Webhook Migration)**: Re-architected the bot from long-polling to a webhook-based setup to resolve the `telegram.error.Conflict` error. This involved modifying `src/main.py` to handle webhook updates and updating `render.yaml` to use `gunicorn` for serving the Flask app, which is the correct and stable approach for Render's free tier.
- **Gunicorn Not Found Error Resolved**: Added `gunicorn` to `requirements.txt` to ensure it is installed during the Render build process, resolving the "command not found" error during deployment.
- **Webhook Not Receiving Messages Resolved**: Relocated the webhook setup logic in `src/main.py` to ensure it is executed when the module is imported by Gunicorn, allowing the bot to receive messages from Telegram.
- **Live API Integration**: The OKX DEX and Gemini APIs have been successfully integrated and tested with live credentials.
- **Dry Run Mode Implemented**: A critical "dry run" feature was implemented to allow for safe, realistic demos using live market data without executing real transactions. This was prioritized to facilitate investor demos.

## 3. Next Steps
1.  **Thoroughly Document Recent Fixes**: Update all memory bank files to reflect the new deployment strategy and the decimal precision fix.
2.  **On-Demand Education**: Begin work on an integrated learning module to explain DeFi concepts on the fly.
3.  **Refine and Document `DRY_RUN_MODE`**: Ensure the `DRY_RUN_MODE` is consistently applied across all new features and document its usage.

## 4. Active Learnings & Insights
- Decimal precision is a critical detail in DeFi applications. Hardcoding values is risky; dynamic lookup is essential.
- Deployment environments (like Render) can have subtle differences from local setups. Understanding how WSGI servers like Gunicorn interact with `asyncio` applications is vital for debugging.
- A stable development environment is a prerequisite for productive feature development. It was necessary to pause and fix the deployment before other work could continue.
