# Full Implementation Plan (Esther) - Detailed

This document enumerates the remaining gaps, technical debt, and placeholders in the current codebase, and proposes concrete implementation steps, tests, and documentation updates. It is explicitly designed to work on Render free tier and PostgreSQL (Render managed).

## Constraints and Principles
- Render free tier (single dyno-style process): background tasks must run within the FastAPI process; keep CPU/memory modest; avoid heavy cron workers.
- PostgreSQL on Render: continue using psycopg2; avoid features that require extensions we haven’t enabled.
- Privacy & security: never store plaintext secrets; continue Fernet encryption; do not execute live swaps by default.
- **Tests-first workflow**: add tests, run locally, commit/push only if green.
- **Git Workflow**: All changes will be committed to the current branch.

## A. Gaps and How We’ll Close Them

### A1. Wallet-backed live trading flow is incomplete
- **Status**: DONE
- **Now**: `/setdefaultwallet` and `/enablelivetrading` implemented; `confirm_swap` validates default wallet when live is enabled (even under DRY_RUN), decrypts key in-memory only for real trades, and consistently passes `chainId`.
- **Guardrails**: Live trading gated by explicit user enablement and default wallet requirement.

### A2. OKX headers and API parity
- **Status**: DONE
- **Now**: `OK-ACCESS-PROJECT` header added in `okx_client.py` when `OKX_PROJECT_ID` is set.

### A3. Token address / decimals handling and symbol resolution
- **Status**: PARTIAL
- **Now**: `tokens` table created and seeded; `TokenResolver` implemented and integrated. Charts correctly special-case BTC via instrument ID using market candles. Remaining: ensure BTC price/quote flows consistently map to WBTC address for EVM swaps.
- **TODO (A3)**:
  - [ ] Add BTC→WBTC aliasing in `TokenResolver.get_token_info()` for EVM/address contexts.
  - [ ] Fallback to constants when DB entry missing; keep charts using instrument ID.
  - [ ] Unit tests: verify `get_price` intent for BTC uses WBTC address/decimals; verify swap paths map BTC→WBTC.
  - [ ] Documentation: note BTC address aliasing in `how-it-works.md` and memory bank.

### A4. Price alerts robustness
- **Status**: PARTIAL
- **Now**: Monitoring uses dynamic decimals and correct imports; OKX client has retries.
- **Next**: Add lightweight rate limiting/backoff in the alert loop.

### A5. Insights use placeholders
- **Status**: TODO
- **Plan**: Pull real snapshot via `PortfolioService.get_snapshot()` and enrich with live prices.

### A6. Portfolio performance persistence cadence
- **Status**: PARTIAL
- **Now**: Idempotent daily saves via ON CONFLICT. 
- **Next**: Add manual `/snapshot` admin command.

### A7. Advanced orders (stop-loss/take-profit)
- **Status**: TODO
- **Plan (phase 2)**: Persist orders in DB; extend monitoring to check and trigger.

### A8. Rebalance plan execution fidelity
- **Status**: TODO
- **Plan**: Per-trade slippage configuration; simulate quotes per leg in DRY_RUN.

### A9. Webhook/polling lifecycle and shutdown
- **Status**: TODO (manual validation)
- **Plan**: Verify startup/shutdown ordering on Render.

### A10. Requirements and docs drift
- **Status**: DONE
- **Now**: Flask removed; PostgreSQL clarified.

### A11. Admin clear-DB endpoint hardening
- **Status**: TODO
- **Plan**: Optional IP allowlist; return 404 for invalid key.

### A12. E2E path for price charts and BTC special-case
- **Status**: PARTIAL
- **Now**: Charts use instrument ID for BTC; E2E added.
- **Next**: Add chain parameter support to handler/intent where relevant.

## B. Database Migrations (Non-breaking)
- `users`: add `default_wallet_id INTEGER NULL REFERENCES wallets(id)`, `live_trading_enabled BOOLEAN DEFAULT FALSE`. (DONE)
- `tokens`: new table for token metadata (`symbol`, `chain_id`, `address`, `decimals`, `PRIMARY KEY(symbol, chain_id)`). (DONE)

## C. Testing Strategy
- Extend unit tests for all new features and fixes. (ONGOING)
- All tests must pass before committing and pushing.

## D. Documentation Updates
- Update `README.md`, `how-it-works.md`, and `okx_dex_api_integration.md` to reflect the changes. (ONGOING)

## E. Phase 1 – Actionable To-Do (1–2 days)
1.  Add BTC→WBTC aliasing (A3) and tests.
2.  Add minimal alert loop backoff (A4).
3.  Update docs accordingly.

## F. Phase 2 – Live Trading & Advanced Orders
1.  Persist and evaluate advanced orders (A7).
2.  Rebalance slippage config and per-leg simulation (A8).
3.  Write tests and update documentation.
