# Error Handling Overhaul Plan

This plan upgrades Esther’s reliability with a robust, test-first error handling strategy. It is split into phases. Each phase includes scope, design, implementation tasks, testing, documentation updates, and version control procedure. After every edit, run the full test suite and ensure green before proceeding.

## Branch & Workflow
- Branch: `feature/error-handling-overhaul`
- Commit early, commit often with scoped changes and passing tests
- Run tests after every file change:
  - `python -m unittest discover -s tests` (or `pytest` if configured)
- Push regularly and open a Draft PR for visibility

---

## Phase 1: Error Taxonomy and Central Handling

### Goals
- Introduce a unified error code taxonomy and a central error handling decorator to prevent stuck conversations and ensure consistent user feedback.

### Design
- `src/error_codes.py`: Enumerate error codes with metadata:
  - `code`, `category` (db, api, nlp, user, unknown), `severity`, `default_user_message`, `remediation_hints`.
- `src/error_handler.py`:
  - `guarded_handler(code: str)` decorator wrapping Telegram handlers.
  - On exception: log with correlation id, clear `context.user_data` for the flow, end the conversation, send a safe, friendly message (fallback text).
  - Global error handler hooked into the bot `Application`.
- Correlation IDs: generate per update and include in structured logs.

### Implementation Tasks
1. Create `src/error_codes.py` with initial codes:
   - `E_DB_CONNECT`, `E_DB_QUERY`, `E_OKX_HTTP`, `E_OKX_API`, `E_TIMEOUT`, `E_NO_DEFAULT_WALLET`, `E_UNKNOWN_INTENT`, `E_TOKEN_RESOLVE`, `E_TG_SEND`, `E_UNKNOWN`.
2. Create `src/error_handler.py` with:
   - `guarded_handler` decorator for async handlers.
   - `add_global_error_handler(app)` that registers a global error handler.
   - Utilities for safe Telegram replies/edits (`safe_reply`, `safe_edit`).
3. Add a simple `correlation.py` that sets a `correlation_id` in a contextvar per update.
4. Wrap key handlers in `src/main.py` with `@guarded_handler(...)`:
   - `buy_token_intent`, `sell_token_intent`, `confirm_swap`, `received_private_key`, `list_wallets`, `portfolio`, `insights`, `get_price_chart_intent`, `portfolio_performance`, `present_next_rebalance_swap`.
5. Ensure all replies in exception paths end with `ConversationHandler.END` and clear state.

### Testing
- New tests: `tests/test_error_handler.py`
  - Decorator converts handler exceptions into friendly messages and ends conversation.
  - State (`context.user_data`) is cleared on error.
  - Global error handler catches unexpected exceptions and replies safely.
- Update existing tests if needed to reflect decorator wrapping.

### Documentation
- Update `how-it-works.md` → add “Error Handling Architecture” section summarizing codes, decorator, and global handler.
- Add `error_handling.md` details explaining codes and mapping to user messages.

### Version Control
- Commit: "phase1: add error taxonomy, central handler, correlation id; wrap core handlers"
- Run tests; ensure green before proceeding.

---

## Phase 2: Conversation Watchdogs and Safe Telegram I/O

### Goals
- Avoid stuck states using timeouts and guarantee safe message sending.

### Design
- State timeouts via `JobQueue`: when entering `AWAIT_*` states, schedule a timeout (e.g., 180s) that ends the flow and sends a guidance message if no progress.
- `safe_reply` and `safe_edit` used everywhere we message the user.

### Implementation Tasks
1. Introduce `HANDLER_TIMEOUT_SECS` env var (default 180).
2. In `src/main.py`, when returning to states like `AWAIT_CONFIRMATION` and `AWAIT_WEB_APP_DATA`, schedule a timeout job keyed by chat/state.
3. Implement `timeout_handler` to cancel state and send a "Still here—do you want to retry or cancel?" message.
4. Migrate direct `reply_text`/`edit_message_text` calls to safe wrappers where appropriate.

### Testing
- New tests: `tests/test_timeouts.py`
  - Simulate state entry and time passage; verify timeout cleans state, ends conversation, and sends message.
- Update main handler tests to assert no behavioral regressions.

### Documentation
- `error_handling.md`: add timeouts policy and configuration.

### Version Control
- Commit: "phase2: add conversation watchdog timeouts and safe telegram I/O"
- Run tests and ensure green before next phase.

---

## Phase 3: Resilient External Calls (Backoff + Circuit Breaker)

### Goals
- Make OKX/Explorer calls resilient and fail fast during outages while providing clear user feedback.

### Design
- Exponential backoff with jitter for HTTP calls.
- Circuit breaker per endpoint (half‑open after `reset_secs`). Short‑circuit when open and surface a friendly message.

### Implementation Tasks
1. Add `src/retry.py` (or use `tenacity`) for backoff helper.
2. Add `src/circuit.py` implementing a small, thread‑safe circuit breaker.
3. Integrate into `src/okx_client.py` and `src/okx_explorer.py`:
   - Wrap GET/POST with backoff; check `breaker.allow()` before call; on failures, `record_failure` and possibly open; on success, `record_success`.
4. Config via env: `CIRCUIT_FAIL_THRESHOLD` (e.g., 5), `CIRCUIT_RESET_SECS` (e.g., 60), `MAX_BACKOFF_SECS`.

### Testing
- New tests: `tests/test_circuit_breaker.py`
  - Trip breaker after threshold, short‑circuit subsequent calls, recover after reset.
- Extend OKX client tests to verify backoff strategy is invoked (mock sleep) and breaker behavior.

### Documentation
- `error_handling.md`: add backoff/CB design and tuning guidance.

### Version Control
- Commit: "phase3: add exponential backoff and circuit breaker to OKX clients"
- Run tests and ensure green.

---

## Phase 4: LLM Failure Advisor (On-Error Only)

### Goals
- Use LLM to convert internal failure context into concise, actionable user guidance without giving LLM orchestration control.

### Design
- `src/failure_advisor.py` with `FailureAdvisor.summarize(error_ctx) -> {message, actions}`.
- Error context includes: error code, user’s last message, intent, entities, stage, hints.
- Advisor optional via `ERROR_ADVISOR_ENABLED=true`.

### Implementation Tasks
1. Implement `FailureAdvisor` using existing `google.generativeai` integration with time and token limits.
2. Wire into `error_handler.py` to be called on exceptions or circuit‑open; if LLM fails, fall back to static messages from `error_codes`.
3. Offer inline buttons for next steps (Retry, Change token, Set default wallet, Help).

### Testing
- `tests/test_failure_advisor.py`
  - Mock Gemini; verify advisor returns message + actions and handler uses them.
  - Ensure fallback path works when advisor errors or disabled.

### Documentation
- `how-it-works.md` and `error_handling.md`: describe advisor role, prompts, privacy considerations.

### Version Control
- Commit: "phase4: integrate FailureAdvisor for on-error guidance"
- Run tests; ensure green.

---

## Phase 5: Background Workers Robustness and User Signals

### Goals
- Ensure monitoring loop continues under failure and inform users on prolonged outages for their alerts.

### Design
- Apply backoff + breaker to `check_alerts` and `sync_all_portfolios` API sections.
- One‑time user notification on persistent failures (rate‑limit, outage), deduplicated per window.

### Implementation Tasks
1. Wrap OKX calls in monitoring with breaker checks.
2. Add a simple deduped notifier for affected users when alerts cannot be evaluated for a configured window.
3. Add health details endpoint to expose breaker states (optional).

### Testing
- Extend `tests/test_monitoring.py`: simulate breaker open and verify no flood of messages, and recovery behavior.

### Documentation
- Update `how-it-works.md` monitoring section with resilience and user signals.

### Version Control
- Commit: "phase5: harden monitoring with breaker and user notifications"
- Run tests.

---

## Phase 6: Documentation & Operational Playbooks

### Goals
- Provide clear developer and support documentation for diagnosing and handling errors in production.

### Tasks
- Expand `error_handling.md` with:
  - Error codes catalogue and mapping to user messages
  - How to enable/disable advisor, tune timeouts, breaker, backoff
  - Logging and correlation IDs usage; sample log queries
- Update `TESTING_GUIDE.md` with new tests and how to run them; guidance for mocking LLM.
- Update `README.md` with environment variables for error handling features.

### Testing
- Docs lint (optional), verify examples compile where applicable.

### Version Control
- Commit: "phase6: documentation and playbooks for error handling"
- Run tests (to ensure no incidental code drift).

---

## Phase 7: Rollout & Observability

### Goals
- Safely deploy with visibility and quick rollback.

### Tasks
- Feature flags: keep advisor disabled on first deploy; enable gradually.
- Add dashboards/alerts for breaker open rate, handler exceptions, timeout activations.
- Post‑deployment bake with increased logging level, then revert to normal.

### Version Control
- Commit and tag: "release: error-handling-overhaul"

---

## Acceptance Criteria Checklist
- No stuck conversations; timeouts end flows with clear guidance
- Centralized error handling with consistent user messages
- OKX calls resilient with backoff and circuit breaker
- FailureAdvisor provides actionable suggestions on errors; safe fallback exists
- Background workers continue and surface prolonged failures once
- All tests green; coverage includes new error paths
- Documentation updated comprehensively 