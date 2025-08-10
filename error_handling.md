# Error Handling Strategy

This document outlines the error handling strategy for the Esther bot. The goal is to provide a consistent and robust way to handle errors, ensuring that users receive clear and helpful feedback while developers get detailed logs for debugging.

## Guiding Principles

1.  **User-Friendly Messages**: Error messages shown to the user should be simple, clear, and actionable. Avoid technical jargon.
2.  **Specific Exceptions**: Use custom exception classes to represent specific error scenarios. This allows for more granular error handling.
3.  **Detailed Logging**: Log errors with as much context as possible to facilitate debugging. This includes the user ID, the command being executed, and the full traceback.
4.  **Fail Gracefully**: The application should handle errors gracefully without crashing.

## Custom Exceptions

All custom exceptions are defined in `src/exceptions.py`.

| Exception                 | Description                                         |
| ------------------------- | --------------------------------------------------- |
| `WalletAlreadyExistsError`  | Raised when a user tries to add a wallet that already exists in the database. |
| `InvalidWalletAddressError` | Raised when a user provides an invalid wallet address. |
| `DatabaseConnectionError`   | Raised when there is an issue connecting to the database. |
| `OKXAPIError`               | Raised when there is an error with the OKX API.     |

## Error Handling Workflow

1.  **Identify Potential Errors**: In the business logic (e.g., in `src/main.py`), wrap code that can raise errors in a `try...except` block.
2.  **Catch Specific Exceptions**: Catch the specific custom exceptions that you expect to be raised.
3.  **Provide User Feedback**: In the `except` block, send a user-friendly message to the user.
4.  **Log the Error**: Log the full exception details for debugging purposes.

### Example

```python
try:
    # Code that might raise an error
    add_wallet_to_database(user_id, wallet_address)
    await update.message.reply_text("Wallet added successfully!")
except WalletAlreadyExistsError:
    await update.message.reply_text("This wallet has already been added.")
    logger.warning(f"User {user_id} tried to add a duplicate wallet.")
except Exception as e:
    await update.message.reply_text("An unexpected error occurred.")
    logger.error(f"An unexpected error occurred for user {user_id}: {e}", exc_info=True)
```

## Adding New Error Types

1.  **Define a New Exception**: Add a new custom exception class to `src/exceptions.py`.
2.  **Raise the Exception**: In the relevant part of the code (e.g., `src/database.py`), raise the new exception when the specific error condition is met.
3.  **Handle the Exception**: Add a new `except` block in the relevant command handler in `src/main.py` to handle the new exception and provide user feedback.

## Trading Error Cases (confirm_swap)

- **Live trading enabled but no default wallet**
  - Message: "Live trading is enabled, but you have not set a default wallet. Please use /setdefaultwallet."
  - Severity: Warning (user action required)
  - Log: info/warning with `telegram_id`

- **Default wallet not found in database**
  - Message: "Your default wallet could not be found. Please set it again."
  - Severity: Warning (data consistency)
  - Log: warning with `telegram_id` and requested `default_wallet_id`

- **Token resolution unavailable (during tests or early runtime)**
  - Mitigation: `TokenResolver` is lazily initialized in `confirm_swap` to prevent `NoneType` errors when the app has not yet run startup hooks.

## Phase 3 Resilience: Backoff and Circuit Breaker

- **Exponential Backoff with Jitter** (`src/retry.py`)
  - All OKX Web3 calls now use exponential backoff with jitter between retries.
  - Configurable via environment variables:
    - `BACKOFF_BASE_SECS` (default 0.2)
    - `BACKOFF_MULTIPLIER` (default 2.0)
    - `BACKOFF_MAX_SECS` (default 5.0)
    - `BACKOFF_JITTER_FRAC` (default 0.1)

- **Circuit Breaker** (`src/circuit.py`)
  - Per-endpoint breaker states: closed → open → half-open → closed.
  - Opens after N consecutive failures; short-circuits requests while open.
  - After cooldown, transitions to half-open and allows a trial request; success closes the breaker, failure re-opens it.
  - Configurable via environment variables:
    - `CIRCUIT_FAIL_THRESHOLD` (default 5)
    - `CIRCUIT_RESET_SECS` (default 30)
  - Short-circuit responses return a recognizable structure:
    ```json
    {
      "success": false,
      "error": "Service temporarily unavailable (protective pause)",
      "code": "E_OKX_HTTP",
      "circuit": {"endpoint": "...", "state": "open", "retry_after_secs": 30}
    }
    ```

- **Error Codes**
  - Network/HTTP failures are surfaced with `code: E_OKX_HTTP` to reuse existing guards.

These mechanisms ensure handlers can gracefully inform users during upstream outages and retry transient issues without hammering external services.

## Phase 4: LLM-powered FailureAdvisor (`src/failure_advisor.py`)

- **Role**: Translates structured internal error data into a concise, user-friendly message plus 2–3 suggested single-word actions. It is used only on failure paths and never controls application flow.
- **Enablement**: Controlled by `ERROR_ADVISOR_ENABLED` (set to `true` to enable). If disabled or any error occurs, handlers fall back to static messages from `src/error_codes.py`.
- **Integration**: `src/error_handler.py`'s `guarded_handler` builds an `error_context` (keys: `correlation_id`, `handler`, `error_code`, `user_message`, optional `intent`, `entities`, `circuit_state`) and calls `FailureAdvisor.summarize(...)`.
- **Replies with Actions**: When advice includes `actions`, the reply renders inline buttons with `callback_data` formatted as `action:<action>`, lowercased (e.g., `action:retry`).
- **Prompt Design**: The advisor uses a precise, role-based prompt to produce strictly JSON output with `message` and `actions`. It instructs the model to keep the message non-technical and succinct, and to choose actions from a small, known set.
- **Privacy**: Only minimal, non-sensitive structured context is sent (error code, intent name, entities, breaker state). Raw user PII and secrets are never included.

### Environment Variables

- `ERROR_ADVISOR_ENABLED`: Toggle LLM FailureAdvisor (default: `false`).
