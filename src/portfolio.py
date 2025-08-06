import logging
from decimal import Decimal
from typing import Dict, List

from src.database import get_db_connection
from src.okx_explorer import OKXExplorer
from src.constants import TOKEN_DECIMALS

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
    def sync_balances(self, telegram_id: int) -> bool:
        """Pull latest on-chain balances for every wallet of *telegram_id*.

        This now consults the OKX DEX API, which can query multiple chains at once.
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

                # 3. Fetch all user wallets and chains
                cur.execute("SELECT address, chain_id FROM wallets WHERE user_id = %s;", (user_pk,))
                wallet_rows = cur.fetchall()
                if not wallet_rows:
                    logger.info("User %s has no wallets – skipping sync", telegram_id)
                    return True  # nothing to sync but not an error

                # Clear previous holdings (simple strategy)
                cur.execute("DELETE FROM holdings WHERE portfolio_id = %s;", (portfolio_id,))

                # We can query all wallets and chains in a single API call.
                all_addresses = [row[0] for row in wallet_rows]
                all_chains = sorted(list(set(str(row[1]) for row in wallet_rows)))

                for address in all_addresses:
                    resp = self.explorer.get_all_balances(address, chains=all_chains)
                    if resp.get("success"):
                        # The response is a list of chains, each with a list of assets
                        for chain_data in resp["data"]:
                            chain_id = int(chain_data.get("chainIndex"))
                            for asset in chain_data.get("tokenAssets", []):
                                self._upsert_holding(cur, portfolio_id, chain_id, asset)
                    else:
                        logger.error("Failed to fetch balances for %s: %s", address, resp.get("error"))

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
    def suggest_rebalance(self, telegram_id: int, target_alloc: Dict[str, float] | None = None) -> List[Dict]:
        """Generate a naïve rebalance plan to reach *target_alloc*.

        target_alloc – mapping symbol -> desired % allocation (sums to 100).
        If None, assume equal weight across existing tokens.

        Returns list of trades of the form
        {"from": symbol_a, "to": symbol_b, "from_amount": float, "usd_amount": float}.
        Only single hop suggestions are returned; caller can translate into swaps.
        """
        snap = self.get_snapshot(telegram_id)
        total = Decimal(str(snap.get("total_value_usd", 0)))
        if total == 0:
            return []

        assets = {a["symbol"]: {"value_usd": Decimal(str(a["value_usd"])), "quantity": Decimal(str(a["quantity"]))} for a in snap["assets"]}

        if not target_alloc:
            # Equal allocation among current holdings
            count = len(assets)
            if count == 0:
                return []
            target_alloc = {sym: 100 / count for sym in assets}

        # Ensure target percentages sum to 100
        total_target = sum(target_alloc.values())
        if abs(total_target - 100) > 0.01:
            # Normalise
            target_alloc = {k: v * 100 / total_target for k, v in target_alloc.items()}

        diffs: Dict[str, Decimal] = {}
        for sym, data in assets.items():
            current_pct = (data["value_usd"] / total) * 100
            desired = Decimal(str(target_alloc.get(sym, 0)))
            diffs[sym] = current_pct - desired  # positive -> overweight

        # Tokens not currently held but in target => underweight
        for sym, pct in target_alloc.items():
            if sym not in diffs:
                diffs[sym] = Decimal("-") + Decimal(str(pct))

        # Build lists
        over = {s: d for s, d in diffs.items() if d > 0}
        under = {s: -d for s, d in diffs.items() if d < 0}
        if not under or not over:
            return []  # already balanced

        plan: List[Dict] = []
        # Simple greedy: convert each overweight token into the single most underweight token
        most_under_symbol = max(under, key=under.get)
        for sym, pct_excess in over.items():
            usd_excess = (pct_excess / 100) * total
            
            # Calculate from_amount
            from_amount = 0.0
            if assets[sym]["value_usd"] > 0:
                price = assets[sym]["value_usd"] / assets[sym]["quantity"]
                from_amount = usd_excess / price

            plan.append({
                "from": sym,
                "to": most_under_symbol,
                "from_amount": float(round(from_amount, 6)),
                "usd_amount": float(round(usd_excess, 2))
            })

        return plan

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _upsert_holding(self, cur, portfolio_id: int, chain_id: int, entry: dict):
        """Insert single holding row derived from DEX API balance entry."""
        symbol = entry.get("symbol", "UNKNOWN")
        token_address = entry.get("tokenContractAddress", "0x")
        balance_str = entry.get("balance", "0")
        # Use the correct number of decimals for the token
        decimals = TOKEN_DECIMALS.get(symbol.upper(), 18)
        try:
            # The API gives balance as a float string, so convert to Decimal directly
            quantity = Decimal(balance_str) * (Decimal(10) ** decimals)  # Store as raw integer
        except Exception:
            quantity = Decimal("0")

        price_usd = Decimal(str(entry.get("tokenPrice", "0")))
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
