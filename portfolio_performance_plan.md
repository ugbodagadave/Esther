# Plan: Portfolio Performance Tracker

This document outlines the detailed plan for implementing the "Portfolio Performance Tracker" feature in Esther.

## 1. Feature Overview

The Portfolio Performance Tracker will enable users to analyze the historical performance of their crypto assets. Users will be able to ask natural language questions to understand how their portfolio has performed over various timeframes.

**User Stories:**
- "How has my portfolio performed over the last 7 days?"
- "Show me the performance of my ETH holdings this month."
- "What is my best-performing asset this week?"

## 2. OKX DEX API Integration

This feature will be powered by the following OKX DEX API endpoints:

- **`GET /api/v5/dex/historical-index-price`** (New Integration): To fetch historical price data for tokens in the user's portfolio.
- **`GET /api/v5/dex/balance/all-token-balances-by-address`** (Existing Integration): To get the current value of the user's assets for comparison.

## 3. Implementation Details

### 3.1. Database Schema

A new table named `portfolio_history` will be added to the PostgreSQL database to store daily snapshots of portfolio value.

**`portfolio_history` table schema:**
```sql
CREATE TABLE portfolio_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total_value_usd NUMERIC NOT NULL,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, snapshot_date)
);
```

### 3.2. Backend Logic

- **`src/okx_client.py`**:
    - A new function `get_historical_price()` will be added to call the `/api/v5/dex/historical-index-price` endpoint.

- **`src/database.py`**:
    - A new function `save_portfolio_snapshot()` will be created to record the total portfolio value in the `portfolio_history` table.

- **`src/portfolio.py`**:
    - The `PortfolioService` will be enhanced with a new function `get_portfolio_performance(user_id, period_days)`.
    - This function will:
        1. Fetch the current portfolio value.
        2. Fetch the historical portfolio value from the `portfolio_history` table for the specified period.
        3. Calculate the percentage change and absolute gain/loss.
        4. Return a summary of the performance.

- **`src/monitoring.py`**:
    - The existing background job that syncs portfolios will be updated to also call `save_portfolio_snapshot()` once daily for each user.

### 3.3. Conversational Flow

- **`src/nlp.py`**:
    - A new intent, `get_portfolio_performance`, will be added to the NLP model to recognize user requests for performance data.
    - The model will be trained to extract entities such as the time period (e.g., "7 days," "last month").

- **`src/main.py`**:
    - A new command handler, `portfolio_performance()`, will be created.
    - This handler will be triggered by the `get_portfolio_performance` intent.
    - It will call the `PortfolioService` to get the performance data and then format it into a user-friendly message.

## 4. Testing Strategy

### 4.1. Unit Tests

- **`tests/test_okx_client.py`**: New tests for the `get_historical_price()` function, including mocked API responses.
- **`tests/test_database.py`**: New tests for the `save_portfolio_snapshot()` function.
- **`tests/test_portfolio.py`**: New tests for the `get_portfolio_performance()` function, covering various scenarios (e.g., positive/negative performance, different time periods).

### 4.2. Integration Tests

- **`e2e_test.py`**: New end-to-end tests will be added to simulate a user asking for their portfolio performance and verify the entire workflow.

## 5. Documentation

- **`README.md`**: The "Core Functionalities" section will be updated to include the new Portfolio Performance Tracker feature.
- **`how-it-works.md`**: The technical documentation will be updated to describe the new data flow and components.
- **`TESTING_GUIDE.md`**: New test cases will be added to guide users on how to test the new feature.

## 6. Version Control

- A new Git branch named `feature/portfolio-performance` will be created for this feature.
- All commits will follow the established conventions, with clear and descriptive messages.
- The branch will be merged into `main` only after all tests have passed and the feature has been manually verified by the user.
