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
- **Current**: `confirm_swap` uses `TEST_WALLET_ADDRESS` from env. Private keys are encrypted and stored but never used for signing. Cross-chain params are partially ignored.
- **Plan**:
  1.  **DB Migration**: Add `users.default_wallet_id` (nullable `INTEGER`, `FOREIGN KEY` to `wallets.id`) and `users.live_trading_enabled` (`BOOLEAN`, `DEFAULT FALSE`).
  2.  **User Settings**: Implement `/setdefaultwallet` and `/enablelivetrading` commands.
  3.  **Update `confirm_swap`**:
      - Resolve `wallet_address` from the designated wallet.
      - For `DRY_RUN=false`, fetch and decrypt the private key in-memory.
      - Call OKX DEX aggregator with the signed transaction.
  4.  **Guardrails**: Require explicit `/enable_live_trading` command.
  5.  **Cross-chain**: Pass `chainId` consistently.
- **Testing & Version Control**:
    - **Test**: Write unit tests for DB migrations, wallet resolution, and live trading guards.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(trading): implement live trading flow"`
        - `git push`

### A2. OKX headers and API parity
- **Current**: `OK-ACCESS-PROJECT` header is missing in `okx_client.py`.
- **Plan**: Add the header to `okx_client.py` requests if `OKX_PROJECT_ID` is set.
- **Testing & Version Control**:
    - **Test**: Extend OKX client header tests.
    - **Git**:
        - `git add .`
        - `git commit -m "fix(okx): add OK-ACCESS-PROJECT header to client"`
        - `git push`

### A3. Token address / decimals handling and symbol resolution
- **Current**: Hardcoded `TOKEN_ADDRESSES` and `TOKEN_DECIMALS`.
- **Plan**:
  1.  **DB Table**: Create `tokens(symbol, chain_id, address, decimals)`.
  2.  **Resolver**: Introduce a token metadata resolver.
  3.  **Dynamic Resolution**: Patch `get_price` and swap flows to use the resolver.
  4.  **Normalize BTC**: Use WBTC on EVM for quotes.
- **Testing & Version Control**:
    - **Test**: Unit tests for resolver and `get_price` correctness.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(token): implement dynamic token resolution"`
        - `git push`

### A4. Price alerts robustness
- **Current**: Uses `1 ETH` for all symbols; missing imports.
- **Plan**:
  1.  **Fix Imports**: Add `TOKEN_ADDRESSES` import in `monitoring.py`.
  2.  **Dynamic Quotes**: Quote minimal representative amount for each token.
  3.  **Rate Limiting**: Add rate limiting and backoff.
- **Testing & Version Control**:
    - **Test**: Alert evaluation tests for varied decimals.
    - **Git**:
        - `git add .`
        - `git commit -m "fix(monitoring): improve price alert robustness"`
        - `git push`

### A5. Insights use placeholders
- **Current**: Portfolio and trend are mocked.
- **Plan**:
  - Pull real snapshot via `PortfolioService.get_snapshot`.
  - Enrich with live prices via OKX.
- **Testing & Version Control**:
    - **Test**: Mock snapshot data and verify prompt content.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(insights): use real data for portfolio insights"`
        - `git push`

### A6. Portfolio performance persistence cadence
- **Current**: Snapshot saved once per day; no backfill.
- **Plan**:
  - Add idempotent “today already saved” check.
  - Add manual `/snapshot` admin command.
- **Testing & Version Control**:
    - **Test**: Ensure duplicate same-day inserts update value.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(portfolio): add manual snapshot and idempotent saves"`
        - `git push`

### A7. Advanced orders (stop-loss/take-profit)
- **Current**: Only acknowledgements.
- **Plan (phase 2)**: Persist orders in DB; extend monitoring to check conditions.
- **Testing & Version Control**:
    - **Test**: DB tests for create/list/trigger logic.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(orders): implement advanced order persistence"`
        - `git push`

### A8. Rebalance plan execution fidelity
- **Current**: Greedy single-hop; no slippage config.
- **Plan**: Allow per-trade slippage configuration; simulate quotes per leg in `DRY_RUN`.
- **Testing & Version Control**:
    - **Test**: Unit tests for slippage plumbing.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(rebalance): add slippage configuration"`
        - `git push`

### A9. Webhook/polling lifecycle and shutdown
- **Current**: Polling branch calls `bot_app.updater.start_polling()` and `bot_app.start()`.
- **Plan**: Verify FastAPI startup/shutdown ordering on Render.
- **Testing & Version Control**:
    - **Test**: Manual smoke test on Render.
    - **Git**: No code changes, no commit.

### A10. Requirements and docs drift
- **Current**: `Flask[async]` in requirements; MongoDB mentioned in `plan.md`.
- **Plan**: Remove `Flask[async]`; clarify PostgreSQL everywhere.
- **Testing & Version Control**:
    - **Test**: CI install check; run full tests.
    - **Git**:
        - `git add .`
        - `git commit -m "chore(deps): remove Flask and clarify PostgreSQL usage"`
        - `git push`

### A11. Admin clear-DB endpoint hardening
- **Current**: Guarded by secret only.
- **Plan**: Add optional IP allowlist; return 404 if key invalid.
- **Testing & Version Control**:
    - **Test**: Unit tests for guard logic.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(admin): harden clear-db endpoint"`
        - `git push`

### A12. E2E path for price charts and BTC special-case
- **Current**: Chain hardcoded to 1 for charts.
- **Plan**: Continue charts on ETH chain; use market candles for BTC.
- **Testing & Version Control**:
    - **Test**: Add chain param tests.
    - **Git**:
        - `git add .`
        - `git commit -m "feat(charts): add chain parameter support"`
        - `git push`

## B. Database Migrations (Non-breaking)
- `users`: add `default_wallet_id INTEGER NULL REFERENCES wallets(id)`, `live_trading_enabled BOOLEAN DEFAULT FALSE`.
- `tokens`: new table for token metadata (`symbol`, `chain_id`, `address`, `decimals`, `PRIMARY KEY(symbol, chain_id)`).

## C. Testing Strategy
- Extend unit tests for all new features and fixes.
- All tests must pass before committing and pushing.

## D. Documentation Updates
- Update `README.md`, `how-it-works.md`, and `okx_dex_api_integration.md` to reflect the changes.

## E. Phase 1 – Actionable To-Do (1–2 days)
1.  Add `OK-ACCESS-PROJECT` header to `okx_client.py`.
2.  Fix monitoring imports and per-symbol quote amount.
3.  Create `tokens` table and a simple resolver.
4.  Normalize price query to use dynamic decimals.
5.  Remove `Flask[async]` from requirements.
6.  Write tests for all the above.
7.  Update documentation.

## F. Phase 2 – Live Trading & Advanced Orders
1.  Implement live trading flow.
2.  Persist and evaluate advanced orders.
3.  Write tests and update documentation.
