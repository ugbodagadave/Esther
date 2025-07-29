# Portfolio Management Module – Implementation Plan

> **Objective**: Deliver real-time portfolio tracking, performance reporting, diversification analysis, and rebalancing suggestions for every Esther user **using only OKX Web3 / DEX API**.
>
> **Guiding Principles**:  
> • Follow the *Test-First Git Workflow* rule – no failing tests may reach `main`.  
> • Respect global coding standards & security guidelines.  
> • Keep PRD success-metrics in sight.

---

## 0. Prerequisites
1. Obtain OKX Web3 API key with Explorer permissions.
2. Add new env vars to `.env` ( `OKX_BASE_URL` optional).
3. Verify existing test suite passes (`pytest`).

---

## 1. Database Layer
| Step | Action | Tests |
|------|--------|-------|
|1.1|Create migration **`v2__portfolio_tables.sql`** <br/>Tables: `portfolios`, `holdings`, `prices`|• Migration applies w/o error <br/>• Tables exist & constraints validated|
|1.2|Add helper in `database.py` → `run_migrations()` (Alembic or raw SQL)|• Unit test: `run_migrations()` idempotent|

---

## 2. OKX Explorer Wrapper
| Step | Action | Tests |
|------|--------|-------|
|2.1|New file `src/okx_explorer.py` with class `OKXExplorer`|—|
|2.2|Implement methods: <br/>`get_native_balance`, `get_token_balances`, `get_spot_price`, `get_kline`|• Mocked HTTP responses verify JSON parsing & error handling|

---

## 3. Portfolio Service (Core Logic)
| Step | Action | Tests |
|------|--------|-------|
|3.1|New file `src/portfolio.py` with `PortfolioService`|—|
|3.2|`sync_balances(user_id)` → writes into `holdings`, updates `last_synced`|• DB fixture → assert rows written, decimals respected|
|3.3|`get_snapshot(user_id)` → returns dict with USD valuation|• Given mock prices, value math correct|
|3.4|`get_performance(user_id, window)` – ROI & P&L|• Uses seeded `prices` rows → expected output|
|3.5|`suggest_rebalance(user_id, target_alloc)`|• Given imbalance, suggestions list correct token deltas|

---

## 4. Telegram Bot Integration
| Step | Action | Tests |
|------|--------|-------|
|4.1|Add `/portfolio` command in `main.py`|• Bot unit-test with PTB `Application.test_session()` returns markdown with totals|
|4.2|Inline buttons: “Report 📈” → calls performance; “Rebalance 🔄” → enters confirmation workflow|• Callback tests ensure correct state transitions|

---

## 5. Background Sync Worker
| Step | Action | Tests |
|------|--------|-------|
|5.1|Create `portfolio_worker.py` (async loop) <br/>Every 10 min → all users → `sync_balances`|• Integration test with mocked Explorer runs one cycle successfully|

---

## 6. Analytics Enhancements
6.1 Diversification analysis – map token → sector via `token/info`.  
6.2 Flag risk ( >50 % in one asset ).  
Tests: deterministic sector map → expected alerts.

---

## 7. Rebalance Execution
7.1 Extend existing swap flow: when called from PortfolioService, build list of `execute_swap` calls.  
7.2 Re-use DRY_RUN_MODE for preview.  
Tests: generate quote per leg, aggregate slippage.

---

## 8. Documentation & Examples
8.1 Update `README.md` & `how-it-works.md`.  
8.2 Add `docs/portfolio_examples.md` with screenshots.

---

## 9. Deployment
9.1 Add env var check in `render.yaml`.  
9.2 Health-check extended to `/portfolio/health` route.

---

## 10. Acceptance Checklist
- [ ] All new unit & integration tests ≥ 90 % coverage for module.  
- [ ] `pytest` green locally & in CI.  
- [ ] Manual smoke-test on staging bot.

---

## Appendix A – OKX Endpoints Reference
```
GET /api/v5/explorer/address/balance
GET /api/v5/explorer/address/token_balance
GET /api/v5/explorer/market/token_ticker
GET /api/v5/explorer/market/kline
```

## Appendix B – Estimated Timeline
| Phase | Duration |
|-------|----------|
|DB & migrations|0.5 d|
|Explorer wrapper|1 d|
|PortfolioService (sync)|1 d|
|Bot command & UI|1 d|
|Worker + analytics|2 d|
|Rebalance engine|2 d|
|Testing + docs|2 d|
|**Total**|≈ 9 dev-days| 