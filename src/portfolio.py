import logging
from decimal import Decimal
from typing import Dict, List

from src.database import get_db_connection
from src.okx_explorer import OKXExplorer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class PortfolioService:
    """High-level portfolio utilities (sync + snapshot)."""

    def __init__(self, explorer: OKXExplorer | None = None):
        self.explorer = explorer or OKXExplorer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def sync_balances(self, telegram_id: int, chain_id: int = 1) -> bool:
        """Pull latest on-chain balances for every wallet of *telegram_id*.

        Returns ``True`` on success, ``False`` otherwise.
        """
        conn = get_db_connection()
        if conn is None:
            return False

        try:
            with conn.cursor() as cur:
                # 1. Resolve internal user id
                cur.execute("SELECT id FROM users WHERE telegram_id = %s;", (telegram_id,))
                result = cur.fetchone()
                if result is None:
                    logger.warning("sync_balances: unknown user %s", telegram_id)
                    return False
                user_pk = result[0]

                # 2. Ensure portfolio row exists
                cur.execute("SELECT id FROM portfolios WHERE user_id = %s;", (user_pk,))
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO portfolios (user_id) VALUES (%s) RETURNING id;", (user_pk,)
                    )
                    portfolio_id = cur.fetchone()[0]
                else:
                    portfolio_id = row[0]

                # 3. Fetch all user wallets
                cur.execute("SELECT address FROM wallets WHERE user_id = %s;", (user_pk,))
                wallet_rows = cur.fetchall()
                if not wallet_rows:
                    logger.info("User %s has no wallets – skipping sync", telegram_id)
                    return True  # nothing to sync but not an error

                # Clear previous holdings (simple strategy)
                cur.execute("DELETE FROM holdings WHERE portfolio_id = %s;", (portfolio_id,))

                for (wallet_address,) in wallet_rows:
                    # 3a native balance
                    native_resp = self.explorer.get_native_balance(wallet_address, chain_id=chain_id)
                    if native_resp.get("success"):
                        for entry in native_resp["data"]:
                            self._upsert_holding(cur, portfolio_id, chain_id, entry)
                    # 3b token balances
                    tok_resp = self.explorer.get_token_balances(wallet_address, chain_id=chain_id)
                    if tok_resp.get("success"):
                        for entry in tok_resp["data"]:
                            self._upsert_holding(cur, portfolio_id, chain_id, entry)

                # Update last_synced timestamp
                cur.execute(
                    "UPDATE portfolios SET last_synced = CURRENT_TIMESTAMP WHERE id = %s;",
                    (portfolio_id,),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error("sync_balances error for user %s: %s", telegram_id, e)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_snapshot(self, telegram_id: int) -> Dict:
        """Return structured portfolio snapshot with USD valuation."""
        conn = get_db_connection()
        if conn is None:
            return {}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT h.symbol, h.amount, h.decimals, h.value_usd
                    FROM holdings h
                    JOIN portfolios p ON h.portfolio_id = p.id
                    JOIN users u ON p.user_id = u.id
                    WHERE u.telegram_id = %s;
                    """,
                    (telegram_id,),
                )
                rows = cur.fetchall()
                assets: List[Dict] = []
                total_value = Decimal("0")
                for symbol, amount, decimals, value_usd in rows:
                    amt_dec = amount if isinstance(amount, Decimal) else Decimal(str(amount))
                    qty = amt_dec / (Decimal(10) ** (decimals or 18))
                    assets.append({
                        "symbol": symbol,
                        "quantity": float(qty),
                        "value_usd": float(value_usd or 0),
                    })
                    val_dec = value_usd if isinstance(value_usd, Decimal) else Decimal(str(value_usd or 0))
                    total_value += val_dec
                return {"total_value_usd": float(total_value), "assets": assets}
        except Exception as e:
            logger.error("get_snapshot error: %s", e)
            return {}
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------
    def get_diversification(self, telegram_id: int) -> Dict:
        """Return portfolio allocation per token symbol (percentage of USD value)."""
        snap = self.get_snapshot(telegram_id)
        total = snap.get("total_value_usd", 0)
        assets = snap.get("assets", [])
        if total == 0:
            return {}
        alloc = {a["symbol"]: round(a["value_usd"] / total * 100, 2) for a in assets}
        return alloc

    def get_roi(self, telegram_id: int, window_days: int = 30) -> float:
        """Calculate simple ROI over *window_days* based on historical price data.

        ROI = (current_value - past_value) / past_value
        This is a naive implementation for illustration/testing.
        """
        snap = self.get_snapshot(telegram_id)
        current_total = Decimal(str(snap.get("total_value_usd", 0)))
        if current_total == 0:
            return 0.0

        past_total = Decimal("0")
        for asset in snap.get("assets", []):
            symbol = asset["symbol"]
            qty = Decimal(str(asset["quantity"]))

            price_resp = self.explorer.get_kline(symbol, bar="1D", limit=window_days + 1)
            if price_resp.get("success") and price_resp["data"]:
                # Use the first element (earliest) as past price open
                past_price = Decimal(str(price_resp["data"][0].get("open", "0")))
                past_total += qty * past_price

        if past_total == 0:
            return 0.0
        roi = (current_total - past_total) / past_total
        return float(round(roi, 4))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _upsert_holding(self, cur, portfolio_id: int, chain_id: int, entry: dict):
        """Insert single holding row derived from Explorer entry dict."""
        symbol = entry.get("symbol") or entry.get("tokenSymbol") or "UNKNOWN"
        token_address = entry.get("tokenAddress") or entry.get("address") or "0x"
        balance_str = entry.get("balance") or entry.get("amount") or "0"
        decimals = int(entry.get("tokenDecimal") or entry.get("decimals") or 18)
        try:
            quantity = Decimal(balance_str)
        except Exception:
            quantity = Decimal("0")

        # Fetch spot price once per symbol (could cache within sync run)
        price_resp = self.explorer.get_spot_price(symbol)
        price_usd = Decimal("0")
        if price_resp.get("success") and price_resp["data"]:
            try:
                price_usd = Decimal(price_resp["data"][0].get("last", "0"))
            except Exception:
                price_usd = Decimal("0")
        value_usd = (quantity / (Decimal(10) ** decimals)) * price_usd

        cur.execute(
            """
            INSERT INTO holdings (portfolio_id, chain_id, token_address, symbol, amount, decimals, value_usd)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                portfolio_id,
                chain_id,
                token_address,
                symbol,
                str(quantity),
                decimals,
                str(value_usd),
            ),
        ) 