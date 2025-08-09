# A simple, hardcoded map for common token symbols to their Ethereum addresses
# We map BTC to WBTC address as it's the token used in DeFi swaps.
TOKEN_ADDRESSES = {
    "ETH": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "BTC": "BTC-USD",  # Use the instrument ID for BTC
    "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "MATIC": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
}

# Map of token symbols to their decimal precision
TOKEN_DECIMALS = {
    "ETH": 18,
    "USDC": 6,
    "USDT": 6,
    "WBTC": 8,
    "BTC": 8,  # WBTC has 8 decimals
    "DAI": 18,
    "MATIC": 18,
}

CHAIN_ID_MAP = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
}

import os

# Global flag for simulation mode, configurable via .env file
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "True").lower() in ("true", "1", "t")
OKX_PROJECT_ID = os.getenv("OKX_PROJECT_ID")
