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
