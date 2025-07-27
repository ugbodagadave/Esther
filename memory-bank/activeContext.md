# Active Context: Esther

## 1. Current Focus
The current focus is wrapping up the initial development phase and preparing for the next set of features. The core foundation of the bot is complete and stable.

## 2. Recent Changes & Decisions
- **Database Switch**: The project was successfully migrated from a planned MongoDB implementation to PostgreSQL to better leverage Render's free tier.
- **Deployment Issues Resolved**: A series of deployment issues on Render were diagnosed and fixed. After a failed attempt at a webhook-based architecture, the application was reverted to a more stable polling mechanism. The Flask web server now runs in a background thread to handle health checks, while the main thread is dedicated to the bot's polling process.
- **Live API Integration**: The OKX DEX and Gemini APIs have been successfully integrated and tested with live credentials.
- **Dry Run Mode Implemented**: A critical "dry run" feature was implemented to allow for safe, realistic demos using live market data without executing real transactions. This was prioritized to facilitate investor demos.
- **Model Names Corrected**: The Gemini model names were corrected to `gemini-2.5-pro` and `gemini-2.5-flash` as per the user's explicit instructions and official documentation.
- **Sell Order Functionality**: Expanded the NLP model and core logic to handle `sell_token` intents, including a full conversation flow for confirmation.
- **Real-time Price Alerts**: Implemented a background monitoring service to check for and notify users of triggered price alerts.
- **Advanced Orders**: Expanded the NLP model to understand `set_stop_loss` and `set_take_profit` intents.
- **Personalized Market Insights**: Implemented a new `/insights` command that provides users with personalized market analysis and recommendations.

## 3. Next Steps
With the core trading flows, wallet management, and price alerts now implemented, the next steps will focus on hardening the system and preparing for more advanced features:
1.  **On-Demand Education**: Begin work on an integrated learning module to explain DeFi concepts on the fly.
2.  **Refine and Document `DRY_RUN_MODE`**: Ensure the `DRY_RUN_MODE` is consistently applied across all new features and document its usage.
3.  **Real-time Notifications**: Begin work on the observer pattern for real-time market alerts.

## 4. Active Learnings & Insights
- A strong documentation-first approach is critical for a project of this complexity, especially given the reliance on external APIs and AI models.
- Acknowledging the constraints of the deployment environment (Render free tier) early in the process is key to designing a viable and robust system.
