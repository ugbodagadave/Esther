# Plan: Refine and Document DRY_RUN_MODE

This document outlines the detailed plan to refine and document the `DRY_RUN_MODE` feature to ensure it is consistently applied and clearly explained.

## 1. Objective

The goal is to ensure that the `DRY_RUN_MODE` is a robust and reliable feature that prevents accidental real-money transactions during testing and demonstrations. This involves a thorough code review, comprehensive testing, and clear documentation.

## 2. Implementation Phases

### Phase 1: Code Review and Refinement

1.  **Audit `src/okx_client.py`**:
    *   Review every function that makes a transactional API call to the OKX DEX (e.g., `execute_swap`).
    *   Ensure that each of these functions accepts a `dry_run: bool` parameter.
    *   Verify that the global `DRY_RUN_MODE` environment variable is used as the default value for this parameter.
2.  **Audit `src/main.py`**:
    *   Trace the execution flow from the Telegram command handlers (e.g., `confirm_swap`) to the `OKXClient` methods.
    *   Confirm that the `DRY_RUN_MODE` is correctly passed down through the layers of the application.
3.  **Refactor if Necessary**:
    *   If any transactional functions are found to not respect the `DRY_RUN_MODE`, refactor them to include the `dry_run` parameter and logic.

### Phase 2: Comprehensive Testing

1.  **Unit Tests (`tests/test_okx_client.py`)**:
    *   Add specific unit tests for each transactional function in `OKXClient`.
    *   These tests will mock the OKX API and assert that when `dry_run=True`, the function returns a simulated success message without attempting to send a real transaction.
    *   Add corresponding tests for `dry_run=False` to ensure the live transaction logic is still correctly triggered.
2.  **Integration Tests (`tests/test_main.py`)**:
    *   Add integration tests for the conversation handlers that trigger transactions.
    *   These tests will verify that the `DRY_RUN_MODE` setting is correctly passed from the bot's configuration to the `OKXClient`.

### Phase 3: Documentation Update

1.  **Update `README.md`**:
    *   Add a clear and prominent section explaining what `DRY_RUN_MODE` is and how to configure it in the `.env` file.
2.  **Update `how-it-works.md`**:
    *   In the "Execution" section of the data flow, add a detailed explanation of how the `DRY_RUN_MODE` flag alters the behavior of the `execute_swap` function.
3.  **Update `TESTING_GUIDE.md`**:
    *   Add a new section that explains how to test the bot with `DRY_RUN_MODE` enabled to ensure that no real funds are used.
4.  **Update Memory Bank**:
    *   Update `memory-bank/activeContext.md` and `memory-bank/progress.md` to reflect the completion of this task.

## 4. Git Workflow

1.  **Branch**: All work will be done on the existing `feature/rebalance` branch.
2.  **Commits**: Each phase will be a separate, atomic commit with a descriptive message (e.g., `refactor(okx): Ensure consistent dry_run_mode application`, `test(okx): Add comprehensive tests for dry_run_mode`, `docs: Update all documentation for dry_run_mode`).
3.  **Pushing**: The changes will be pushed to the remote `feature/rebalance` branch upon completion of all phases.

This plan will ensure that the `DRY_RUN_MODE` is a reliable and well-documented feature of the Esther AI Agent.
