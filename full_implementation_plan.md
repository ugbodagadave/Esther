# Full Implementation Plan (Esther)

This document enumerates the remaining gaps, technical debt, and placeholders in the current codebase, and proposes concrete implementation steps, tests, and documentation updates. It is explicitly designed to work on Render free tier and PostgreSQL (Render managed). Any proposal that would materially change the stack is called out for approval.

## Constraints and Principles
- Render free tier (single dyno-style process): background tasks must run within the FastAPI process; keep CPU/memory modest; avoid heavy cron workers.
- PostgreSQL on Render: continue using psycopg2; avoid features that require extensions we haven’t enabled.
- Privacy & security: never store plaintext secrets; continue Fernet encryption; do not execute live swaps by default.
- Tests-first workflow: add tests, run locally, commit/push only if green.

## A. Gaps and How We’ll Close Them

### A1. Wallet-backed live trading flow is incomplete
- Current: `confirm_swap` uses `TEST_WALLET_ADDRESS` from env. Private keys are encrypted and stored but never used for signing. Cross-chain params are partially ignored.
- Plan:
  1) Add a user setting to designate a “default trading wallet” per Telegram user. Store the selected `wallet_id` in a new `users.default_wallet_id` column (nullable).
  2) Update `confirm_swap` to resolve `wallet_address` from the designated wallet (fallback to first wallet). For DRY_RUN=false, fetch and decrypt the private key (in-memory only) then call OKX DEX aggregator as designed (note: OKX DEX aggregator typically expects wallet execution; for now we stay with OKX’s swap interface per current client and keep DRY_RUN default true).
  3) Guardrails: require explicit `/enable_live_trading` command with confirmation to flip a per-user flag (new column `users.live_trading_enabled BOOLEAN DEFAULT FALSE`).
  4) Cross-chain: pass `chainId` consistently and reflect `destination_chain_id` only for quotes where supported. If cross-chain bridging requires a different endpoint, we will simulate (DRY_RUN) until approved (INPUT NEEDED).
- Tests:
  - Unit tests for new DB migrations and wallet resolution.
  - Handler tests verifying that when live trading is disabled the bot refuses execution and suggests enabling.
  - Execute swap path in DRY_RUN and LIVE branches (mock HTTP).
- Docs: Update README → “Enabling Live Trading,” security warnings, and DRY_RUN notes.
- INPUT NEEDED: Approve whether we should implement actual on-server signing with stored private keys (higher risk) or require user-side wallet signing via embedded OKX Wallet deep-link.

### A2. OKX headers and API parity
- Current: `OK-ACCESS-PROJECT` header is added in `okx_explorer.py` but not in `okx_client.py`.
- Plan: Add the same header to `okx_client.py` request headers if `OKX_PROJECT_ID` is set; keep backward compatibility.
- Tests: Extend OKX client header tests verifying header presence.
- Docs: Update OKX Integration guide for the header across all endpoints.

### A3. Token address / decimals handling and symbol resolution
- Current: Small hardcoded `TOKEN_ADDRESSES` and `TOKEN_DECIMALS`. BTC maps to `BTC-USD` (instrument) for charts but is used like an address for quotes in some flows. Price checks assume 1 token in smallest unit with fixed decimals.
- Plan:
  1) Introduce a token metadata resolver that can source decimals and addresses for known chains (OKX explorer/token info if available; else curated list). Cache in DB table `tokens(symbol, chain_id, address, decimals)` with upserts.
  2) Patch get_price and swap flows to resolve addresses/decimals dynamically; fall back to curated constants.
  3) Normalize BTC handling: for quotes, use WBTC on EVM when user asks BTC on Ethereum; for charts, continue `BTC-USD` via market candles.
- Tests: Unit tests for resolver, fallbacks, and get_price intent correctness for multiple symbols/decimals.
- Docs: Document resolution rules and supported symbols.

### A4. Price alerts robustness
- Current: Uses `1 ETH` to compute USD price for any symbol; missing import for `TOKEN_ADDRESSES` in monitoring when imported as a module; no per-symbol quote units.
- Plan:
  1) Import `TOKEN_ADDRESSES` (or use resolver) in `monitoring.py`.
  2) Quote minimal representative amount for the specific token using its decimals (e.g., 1 whole token in smallest units or a small notional like $10 equivalent).
  3) Add rate limiting and backoff per alert to stay within free tier limits.
- Tests: Alert evaluation tests for varied decimals; import-safety tests.
- Docs: Update monitoring section in how-it-works.

### A5. Insights use placeholders
- Current: Portfolio inferred from existence of wallets; “trend” mocked.
- Plan:
  - Pull real snapshot via `PortfolioService.get_snapshot` and summarize holdings; enrich with live prices via OKX; remove mocked trend; keep Gemini prompt but based on actual positions.
- Tests: Mock snapshot data and verify prompt content assembled.

### A6. Portfolio performance persistence cadence
- Current: Snapshot saved once per monitoring cycle per day; no backfill.
- Plan: Keep once-per-day snapshot to stay light on free tier; add idempotent “today already saved” check (already covered by UNIQUE). Add manual `/snapshot` admin for backfill if needed.
- Tests: Ensure duplicate same-day inserts update value per ON CONFLICT.

### A7. Advanced orders (stop-loss/take-profit)
- Current: Only acknowledgements.
- Plan (phase 2): Persist advanced orders in DB; extend monitoring to check conditions using quotes; notify user. Execution remains manual confirmation for now (safer, free tier friendly). INPUT NEEDED.
- Tests: DB tests for create/list/trigger logic; monitoring unit tests.

### A8. Rebalance plan execution fidelity
- Current: Greedy single-hop toward the most underweight; execution reuses general swap flow; no slippage config per leg.
- Plan: Allow per-trade slippage configuration; simulate quotes per leg in DRY_RUN and show user expected slippage and path; live execution only when enabled.
- Tests: Unit tests for slippage plumbing and plan presentation.

### A9. Webhook/polling lifecycle and shutdown
- Current: Polling branch calls `bot_app.updater.start_polling()` and `bot_app.start()`; ensure clean shutdown paths.
- Plan: Verify FastAPI startup/shutdown ordering on Render; keep polling default if webhook URL not set.
- Tests: None beyond existing handlers; manual smoke on Render.

### A10. Requirements and docs drift
- Current: `Flask[async]` remains in requirements; docs mention MongoDB in `plan.md` (legacy).
- Plan: Remove `Flask[async]`; clarify PostgreSQL everywhere; keep FastAPI as the only web framework.
- Tests: CI install check; run full tests.

### A11. Admin clear-DB endpoint hardening
- Current: Guarded by secret only.
- Plan: Add optional IP allowlist via env; return 404 if key invalid; add prominent warnings in docs; keep it for dev only.
- Tests: Unit tests for guard logic.

### A12. E2E path for price charts and BTC special-case
- Current: Chain hardcoded to 1 for charts; BTC instrument vs address duality already handled in client.
- Plan: Continue charts on ETH chain when addresses are used; for BTC use market candles; add minimal chain selection support via intent entities later.
- Tests: Already covered by existing chart tests; add chain param tests.

## B. Database Migrations (Non-breaking)
- users: add `default_wallet_id INTEGER NULL REFERENCES wallets(id)`, `live_trading_enabled BOOLEAN DEFAULT FALSE`.
- tokens: new table for token metadata (symbol, chain_id, address, decimals, PRIMARY KEY(symbol, chain_id)).
- Backfill step optional.

## C. Testing Strategy
- Extend unit tests for:
  - OKX client headers and chainId propagation
  - Token resolver
  - Alert evaluator with per-symbol decimals
  - Wallet selection & live trading guardrails
  - Insights prompt sources actual snapshot
  - Requirements sanity (import success)
- Keep all tests runnable on Render free tier (no heavy network; mock HTTP).

## D. Documentation Updates
- README: “Enabling Live Trading,” “Selecting Default Wallet,” “Price Alerts,” “Token Resolution,” “Security.”
- how-it-works.md: update trading flow, monitoring/alerts, and portfolio sections.
- okx_dex_api_integration.md: document `OK-ACCESS-PROJECT` on aggregator endpoints too.

## E. Inputs Needed from You
1) Approve approach for LIVE trading:
   - Option A: Server-side signing with stored encrypted private keys (simpler UX, higher custodial risk)
   - Option B: User-side signing via deep-link to OKX Wallet / injected Web3 (safer, more UX work)
2) Approve that cross-chain swaps remain simulated until OKX-bridge flow is integrated (later phase).
3) Provide `OKX_PROJECT_ID` for headers; confirm supported chains to prioritize.

## F. Phase 1 – Actionable To‑Do (1–2 days)
- Add `OK-ACCESS-PROJECT` header to `okx_client.py`.
- Fix monitoring imports and per-symbol quote amount (use resolver fallback to decimals map).
- Create `tokens` table and a simple resolver with curated seed for ETH/USDC/USDT/WBTC/MATIC/DAI.
- Normalize price query to use dynamic decimals and 1 unit or $10 notional.
- Remove `Flask[async]` from requirements.
- Tests covering the above.
- Docs: Update OKX guide and README sections for the changes.

Deliverables of Phase 1: all tests green, pushed branch, and PR.

## G. Phase 2 – Live Trading & Advanced Orders (needs approval)
- Add `users.default_wallet_id`, `users.live_trading_enabled`, flows to select default wallet and enable live trading.
- Update `confirm_swap` to resolve wallet and guard on live flag.
- Persist and evaluate advanced orders in monitoring.
- More tests & docs.

## H. Render Free Tier Notes
- Keep monitoring loop intervals configurable; default 10 min portfolio sync; alerts check each 60s.
- Avoid extra processes; reuse FastAPI startup task.

## I. Risk & Rollback
- All DB changes idempotent. Feature flags (live trading) default off. DRY_RUN stays default on. 