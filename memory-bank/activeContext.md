# Active Context: Esther

## 1. Current Focus
The current focus is wrapping up the initial development phase and preparing for the next set of features. The core foundation of the bot is complete and stable.

## 2. Recent Changes & Decisions
- **Database Switch**: The project was successfully migrated from a planned MongoDB implementation to PostgreSQL to better leverage Render's free tier.
- **Deployment Issues Resolved**: A series of deployment issues on Render were diagnosed and fixed, resulting in a stable deployment configuration (`render.yaml`) and startup script (`src/main.py`).
- **Live API Integration**: The OKX DEX and Gemini APIs have been successfully integrated and tested with live credentials.
- **Dry Run Mode Implemented**: A critical "dry run" feature was implemented to allow for safe, realistic demos using live market data without executing real transactions. This was prioritized to facilitate investor demos.
- **Model Names Corrected**: The Gemini model names were corrected to `gemini-2.5-pro` and `gemini-2.5-flash` as per the user's explicit instructions and official documentation.
- **Sell Order Functionality**: Expanded the NLP model and core logic to handle `sell_token` intents, including a full conversation flow for confirmation.
- **Real-time Price Alerts**: Implemented a background monitoring service to check for and notify users of triggered price alerts.

## 3. Next Steps
With the core trading flows, wallet management, and price alerts now implemented, the next steps will focus on hardening the system and preparing for more advanced features:
1.  **Refine and Document `DRY_RUN_MODE`**: Ensure the `DRY_RUN_MODE` is consistently applied across all new features and document its usage.
2.  **Expand NLP for Advanced Orders**: Train the NLP model to understand more complex commands, such as setting stop-loss/take-profit orders.
3.  **Personalized Market Insights**: Begin work on proactive trend analysis and portfolio-based recommendations.
4.  **Real-time Notifications**: Begin work on the observer pattern for real-time market alerts.
5.  **Refine `DRY_RUN_MODE`**: Ensure the `DRY_RUN_MODE` flag is respected across all new features to maintain a safe testing environment.

## 4. Active Learnings & Insights
- A strong documentation-first approach is critical for a project of this complexity, especially given the reliance on external APIs and AI models.
- Acknowledging the constraints of the deployment environment (Render free tier) early in the process is key to designing a viable and robust system.
