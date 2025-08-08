# Plan: Simple Price Charts

This document outlines the detailed plan for implementing the "Simple Price Charts" feature in Esther.

## 1. Feature Overview

This feature will enable users to request and view simple price charts for a given token and time period directly within the Telegram chat.

**User Stories:**
- "Show me a 30-day price chart for BTC."
- "Give me a 7-day chart for ETH."
- "I want to see the price chart for SOL for the last 90 days."

## 2. OKX DEX API Integration

This feature will be powered by the following OKX DEX API endpoint:

- **`GET /api/v5/dex/historical-index-price`** (New Integration): To fetch historical price data for the specified token.

## 3. Implementation Details

### 3.1. NLP Enhancement

- **`src/nlp.py`**:
    - A new intent, `get_price_chart`, will be added to the NLP model's prompt.
    - The model will be trained to extract the following entities:
        - `symbol`: The token symbol (e.g., BTC, ETH).
        - `period`: The time period (e.g., "30 days", "7d").

### 3.2. Backend Logic

- **`src/main.py`**:
    - A new handler function, `get_price_chart()`, will be created to handle the `get_price_chart` intent.
    - This function will:
        1. Parse the `period` entity using the existing `_parse_period_to_days` helper function.
        2. Call a new method in the `OKXClient` to fetch the historical price data.
        3. Call a new utility function to generate the chart image.
        4. Send the chart image to the user using the `send_photo` method.

- **`src/okx_client.py`**:
    - A new method, `get_historical_prices()`, will be added to call the `/api/v5/dex/historical-index-price` endpoint.
    - This method will take the token symbol and time period as input and return a list of historical prices.

- **`src/chart_generator.py`** (New File):
    - A new file will be created to house the chart generation logic.
    - A function, `generate_price_chart()`, will be created to:
        1. Take the historical price data as input.
        2. Use the `matplotlib` library to generate a simple line chart.
        3. Save the chart as a PNG image to a temporary file.
        4. Return the path to the image file.

### 3.3. Dependencies

- The `matplotlib` library will be added to the `requirements.txt` file.

## 4. Testing Strategy

### 4.1. Unit Tests

- **`tests/test_nlp.py`**: New tests for the `get_price_chart` intent.
- **`tests/test_okx_client.py`**: New tests for the `get_historical_prices()` method.
- **`tests/test_chart_generator.py`** (New File): New tests for the `generate_price_chart()` function.
- **`tests/test_main.py`**: New tests for the `get_price_chart()` handler function.

### 4.2. Integration Tests

- **`e2e_test.py`**: New end-to-end tests to simulate a user requesting a price chart and verify the entire workflow.

## 5. Documentation

- **`README.md`**: The "Core Functionalities" section will be updated to include the new Simple Price Charts feature.
- **`how-it-works.md`**: The technical documentation will be updated to describe the new data flow and components.
- **`TESTING_GUIDE.md`**: New test cases will be added to guide users on how to test the new feature.
- **`memory-bank/`**: All relevant files in the memory bank will be updated to reflect the new feature.

## 6. Version Control

- A new Git branch named `feature/price-charts` will be created for this feature.
- All commits will follow the established conventions, with clear and descriptive messages.
- The branch will be merged into `main` only after all tests have passed and the feature has been manually verified.
