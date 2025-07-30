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
`OKX_PROJECT_ID` is injected as the additional header `OK-ACCESS-PROJECT`. If this header is missing
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
| `/api/v5/dex/market/candlesticks-history`           | Historical candles used for ROI calculation.                 |

These calls are **GET** requests signed with the same HMAC flow as trading requests and **must** include the `OK-ACCESS-PROJECT` header described above.

### D. Error Handling

The `OKXClient` includes robust error handling to manage potential issues with the API, such as network errors or invalid requests. It uses a retry mechanism to automatically resubmit failed requests, which makes the bot more resilient and reliable.

## 2. Potential for X Layer Integration

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
