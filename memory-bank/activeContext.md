# Active Context: Esther

## 1. Current Focus
- Completed Error Handling Phases 1 & 2 (centralized errors, guards, global handler, timeouts, cancel flow).
- Next: Phase 3 – exponential backoff with jitter and circuit breaker for OKX clients; tests.

## 2. Recent Changes & Decisions
- **Live Trading Settings (Completed)**: `/setdefaultwallet` and `/enablelivetrading` commands and NLP intents wired; DB schema in place.
- **Confirm Swap Hardening**: Early abort when live trading enabled but default wallet missing/not found (even under dry-run); lazy `TokenResolver` init in `confirm_swap`.
- **A4 – Monitoring**: Added per-alert throttle + jitter and error backoff environment variables; updated docs/testing guide.
- **A5 – Insights**: Switched to `PortfolioService.get_snapshot()` for portfolio holdings; kept minimal price enrichment; tests updated to mock snapshot.

## 3. Next Steps
1. Implement Phase 3 resilience (backoff helper + circuit breaker) with unit tests.
2. Phase 4 FailureAdvisor integration for on-error guidance (feature-flagged) and tests.
3. Revisit A6 `/snapshot` after resilience work.

## 4. Active Learnings & Insights
- Validation should reflect user intent state (live enabled) even when environment is in simulation mode.
- Lazy initialization patterns reduce test flakiness when startup hooks aren’t invoked.
- Background throttling + backoff helps avoid API rate limits during alert scans.
