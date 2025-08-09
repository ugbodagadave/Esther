# Active Context: Esther

## 1. Current Focus
- Completed A4 (alert throttling/backoff) and A5 (insights from real snapshots).
- Next: implement A6 `/snapshot` admin command (idempotent daily save) with tests.

## 2. Recent Changes & Decisions
- **Live Trading Settings (Completed)**: `/setdefaultwallet` and `/enablelivetrading` commands and NLP intents wired; DB schema in place.
- **Confirm Swap Hardening**: Early abort when live trading enabled but default wallet missing/not found (even under dry-run); lazy `TokenResolver` init in `confirm_swap`.
- **A4 – Monitoring**: Added per-alert throttle + jitter and error backoff environment variables; updated docs/testing guide.
- **A5 – Insights**: Switched to `PortfolioService.get_snapshot()` for portfolio holdings; kept minimal price enrichment; tests updated to mock snapshot.

## 3. Next Steps
1. Implement `/snapshot` admin command (A6) and unit tests.
2. Plan A7 advanced orders persistence and monitoring checks.
3. Add E2E coverage once `/snapshot` is available.

## 4. Active Learnings & Insights
- Validation should reflect user intent state (live enabled) even when environment is in simulation mode.
- Lazy initialization patterns reduce test flakiness when startup hooks aren’t invoked.
- Background throttling + backoff helps avoid API rate limits during alert scans.
