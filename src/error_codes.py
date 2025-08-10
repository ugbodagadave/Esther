# Centralized error code registry
# Each entry includes a default user-facing message and remediation hints

ERROR_CODES = {
    "E_DB_CONNECT": {
        "category": "db",
        "severity": "high",
        "default_user_message": "I'm having trouble connecting to the database. Please try again later.",
        "remediation_hints": ["Check database connectivity", "Retry operation"],
    },
    "E_DB_QUERY": {
        "category": "db",
        "severity": "medium",
        "default_user_message": "I ran into a database error performing your request.",
        "remediation_hints": ["Retry operation", "Validate inputs"],
    },
    "E_OKX_HTTP": {
        "category": "api",
        "severity": "medium",
        "default_user_message": "The market service is temporarily unavailable. Please try again shortly.",
        "remediation_hints": ["Retry", "Try a different token or period"],
    },
    "E_OKX_API": {
        "category": "api",
        "severity": "low",
        "default_user_message": "The market service returned an error. Please try again.",
        "remediation_hints": ["Retry", "Check token symbol"]
    },
    "E_TIMEOUT": {
        "category": "flow",
        "severity": "low",
        "default_user_message": "This step timed out waiting for a response. Do you want to try again?",
        "remediation_hints": ["Retry", "Start over"],
    },
    "E_NO_DEFAULT_WALLET": {
        "category": "user",
        "severity": "low",
        "default_user_message": "You need to set a default wallet to proceed. Use /setdefaultwallet.",
        "remediation_hints": ["Run /setdefaultwallet"],
    },
    "E_UNKNOWN_INTENT": {
        "category": "nlp",
        "severity": "low",
        "default_user_message": "I didn’t quite catch that. Try ‘price of BTC’ or ‘show my portfolio’.",
        "remediation_hints": ["Clarify request", "Use examples in /help"],
    },
    "E_TOKEN_RESOLVE": {
        "category": "logic",
        "severity": "low",
        "default_user_message": "I don’t recognize that token yet. Try a common symbol like ETH or USDC.",
        "remediation_hints": ["Use supported symbols", "Check spelling"],
    },
    "E_TG_SEND": {
        "category": "telegram",
        "severity": "low",
        "default_user_message": "I couldn’t send a message just now. Please try again.",
        "remediation_hints": ["Retry"],
    },
    "E_UNKNOWN": {
        "category": "unknown",
        "severity": "high",
        "default_user_message": "An unexpected error occurred. Please try again.",
        "remediation_hints": ["Retry", "Contact support if it persists"],
    },
}


def get_user_message(error_code: str) -> str:
    entry = ERROR_CODES.get(error_code) or ERROR_CODES["E_UNKNOWN"]
    return entry["default_user_message"] 