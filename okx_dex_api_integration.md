# OKX DEX API Integration and X Layer Potential

This document provides a detailed overview of how the Esther AI Agent integrates with the OKX DEX API and explores the potential for future integration with X Layer.

## 1. OKX DEX API Integration

The OKX DEX API is the core of Esther's trading functionality. It allows the AI Agent to perform a variety of actions on the OKX DEX aggregator, including fetching market data, getting live quotes, and executing trades.

### A. Authentication

All requests to the OKX Web3 APIs (DEX, Explorer, Market) require **four** pieces of information:

* `OKX_API_KEY`
* `OKX_API_SECRET`
* `OKX_API_PASSPHRASE`
* `OKX_PROJECT_ID` – identifies the *Project* that groups your keys and allocates quota.

The first three values go into the regular `OK-ACCESS-*` headers used across all OKX APIs. The
`OKX_PROJECT_ID` is injected as the additional header `OK-ACCESS-PROJECT`. This is handled automatically by the `OKXClient`. If this header is missing
the DEX and Market endpoints respond with an error.

All four credentials are stored in a `.env` file and loaded at runtime.

### B. Core Functionality

The `src/okx_client.py` module is responsible for all interactions with the OKX DEX API. It includes the following key functions:

-   **`get_live_quote`**: This function fetches a real-time swap quote from the `/api/v5/dex/aggregator/quote` endpoint. It takes the addresses of the "from" and "to" tokens, the amount to be swapped, and an optional `chain_index` as input. This allows for fetching quotes for swaps on different blockchains. It returns a detailed quote that includes the estimated amount of the "to" token that will be received.
-   **`execute_swap`**: This function executes a trade on the OKX DEX. It uses the `/api/v5/dex/aggregator/swap` endpoint to submit a signed transaction to the blockchain. It also accepts an optional `chain_index` to specify the blockchain for the swap. The function includes a "dry run" mode that allows for safe, realistic demos using live market data without executing real transactions.

### C. DEX Balance & Market Endpoints (Read-Only)

Alongside trading endpoints, Esther consumes OKX **Web3 DEX and Market** APIs to power portfolio tracking:

| Endpoint                                            | Purpose                                                      |
|-----------------------------------------------------|--------------------------------------------------------------|
| `/api/v5/dex/balance/all-token-balances-by-address` | Consolidated native and token balances with USD prices.      |
| `/api/v5/market/history-candles`                    | Historical candles for instrument IDs (e.g., BTC-USD).       |
| `/api/v5/wallet/token/historical-price`             | Historical prices for specific token addresses on a chain.   |

These calls are **GET** requests signed with the same HMAC flow as trading requests and **must** include the `OK-ACCESS-PROJECT` header described above.

### D. Error Handling and Retry Logic

The `OKXClient` includes robust error handling to manage potential issues with the API:

- Retry Mechanism: Failed requests are retried (Phase 3 will switch to exponential backoff with jitter)
- Circuit Breaker (Phase 3): Calls short‑circuit during outages and recover after a cool‑down
- HTTP Status Code Handling: Specific handling for common statuses
- Request Validation: Ensures all required parameters are present and properly formatted
- Chain ID Formatting: Automatically converts chain IDs to strings to prevent API formatting errors

### E. Portfolio Integration

The OKX DEX API powers Esther's real-time portfolio tracking:

- **Automatic Balance Sync**: Every 10 minutes, Esther syncs all user wallet balances
- **Multi-Chain Support**: Tracks balances across Ethereum, Polygon, BSC, and other supported chains
- **Real-Time Pricing**: Uses OKX's integrated pricing data for accurate USD valuations
- **Performance Analytics**: Calculates ROI and diversification metrics using historical data

## 2. Natural Language Integration

Esther's integration with OKX DEX API is enhanced by sophisticated natural language processing:

### A. Intent Recognition for Trading

The NLP system can understand various trading intents and route them to appropriate OKX API calls:

- **Price Queries**: "What's the price of ETH?" → Calls OKX market data endpoints
- **Trading Commands**: "Buy 0.1 ETH with USDT" → Initiates quote and swap workflow
- **Portfolio Queries**: "Show me my portfolio" → Triggers balance sync and snapshot generation
- **Rebalance Commands**: "Rebalance my portfolio" → Initiates the rebalance suggestion and execution workflow

### B. Model Selection for API Operations

Esther uses intelligent model selection for different types of OKX API interactions:

- **Gemini 2.5 Flash**: For simple price checks and basic portfolio queries
- **Gemini 2.5 Pro**: For complex trading decisions requiring market analysis

## 3. Security and Best Practices

### A. API Key Management

- **Environment Variables**: All OKX credentials are stored securely in environment variables
- **Encryption**: User-specific API keys are encrypted before database storage
- **Least Privilege**: Only request necessary permissions for bot functionality

### B. Request Signing

- **HMAC Authentication**: All requests are properly signed using OKX's HMAC-SHA256 method
- **Timestamp Validation**: Ensures requests are not replayable
- **Nonce Generation**: Unique nonces prevent request duplication

## 4. Potential for X Layer Integration

X Layer is a high-performance, EVM-compatible Layer 2 network that is designed to make it faster and cheaper to transact with dApps in the OKX ecosystem. Integrating Esther with X Layer would provide a number of significant benefits:

### A. Faster and Cheaper Transactions

By processing transactions on X Layer, Esther would be able to offer its users significantly faster and cheaper trades. This would be a major advantage, especially for high-frequency traders and users who are sensitive to gas fees.

### B. Enhanced Scalability

X Layer is designed to be highly scalable, which would allow Esther to handle a much larger volume of transactions without any degradation in performance. This would be critical for the long-term growth and success of the project.

### C. Access to a Growing Ecosystem

X Layer is a rapidly growing ecosystem with a wide range of dApps and services. By integrating with X Layer, Esther would be able to tap into this ecosystem and offer its users a much richer and more diverse set of features.

### D. How to Implement X Layer Integration

To integrate Esther with X Layer, we would need to make the following changes:

1.  **Update the `OKXClient`**: We would need to update the `OKXClient` to support the X Layer network. This would involve adding a new `chainIndex` parameter to the `get_live_quote` and `execute_swap` functions, which would allow us to specify that the transaction should be processed on X Layer.
2.  **Update the User Interface**: We would need to update the user interface to allow users to select X Layer as their preferred network. This could be done by adding a new option to the settings menu or by prompting the user to select a network when they initiate a trade.
3.  **Update the Smart Contracts**: If Esther were to use its own smart contracts, we would need to deploy them to the X Layer network.

By making these changes, we could seamlessly integrate Esther with X Layer and provide our users with a faster, cheaper, and more scalable trading experience.

## 5. Testing and Validation

### A. Unit Testing

- **Mock OKX API Responses**: Comprehensive unit tests with mocked API responses
- **Error Scenario Testing**: Tests for network failures, rate limiting, and invalid responses
- **Authentication Testing**: Validates proper request signing and header inclusion

### B. End-to-End Testing

- **Live API Testing**: `e2e_test.py` performs real API calls to validate integration
- **Portfolio Sync Testing**: Verifies balance discovery and valuation accuracy
- **Trading Workflow Testing**: Tests complete quote-to-execution flow

### C. Performance Monitoring

- **Response Time Tracking**: Monitors API response times and retry frequency
- **Error Rate Monitoring**: Tracks API error rates and success percentages
- **Rate Limit Management**: Ensures compliance with OKX API rate limits

## 6. X Layer Integration Potential (Concise)

X Layer is OKX’s zkEVM Layer‑2 built with Polygon CDK, designed for low fees and full EVM compatibility with OKB as the native gas token.

- What it is: A ZK‑powered Ethereum L2 using Polygon CDK; fully EVM compatible. Sources: [X Layer overview](https://www.okx.com/xlayer), [X Layer public mainnet announcement](https://www.okx.com/learn/x-layer-mainnet), [X Layer developer docs](https://github.com/okx/xlayer-docs).
- Why it matters for Esther: Cheaper swaps, faster confirmations, and direct alignment with OKX’s Web3 stack (DEX, Wallet, Bridge, Explorer).

### How Esther would integrate X Layer

1) Quote & swap calls
- Pass X Layer’s chain identifier to the existing OKX Aggregator endpoints used in `OKXClient`.
- No code rewrite for contracts is needed due to EVM compatibility; token resolution remains address/decimals‑driven.

2) Portfolio tracking
- Include X Layer in the balance sync by querying the same OKX Web3 DEX/Explorer endpoints for the user’s address on X Layer.

3) UI & NLP
- Allow users to target X Layer explicitly (e.g., “buy 10 OKB on X Layer”).
- Map “X Layer” to the appropriate chain parameter internally.

4) Bridging (optional UX enhancement)
- Offer a convenience deep‑link to OKX Bridge for users funding X Layer the first time.

5) Security & ops
- Continue signing with the standard OKX headers (`OK-ACCESS-*` + `OK-ACCESS-PROJECT`).
- DRY‑RUN behavior remains unchanged.

This approach keeps Esther’s current architecture intact while unlocking lower‑cost execution paths on X Layer.

> Note: The in-chat Help menu has been refreshed for clearer human reading (bulleted items, no backticks).
