"""
Custom exception classes for the application.
"""

class WalletAlreadyExistsError(Exception):
    """Raised when a user tries to add a wallet that already exists in the database."""
    pass

class InvalidWalletAddressError(Exception):
    """Raised when a user provides an invalid wallet address."""
    pass

class DatabaseConnectionError(Exception):
    """Raised when there is an issue connecting to the database."""
    pass

class OKXAPIError(Exception):
    """Raised when there is an error with the OKX API."""
    pass
