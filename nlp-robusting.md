# Plan for Enhancing Esther's Natural Language Capabilities

## 1. Introduction
The goal of this initiative is to transition Esther from a command-driven bot to a sophisticated, conversational AI. This involves two core streams of work:
1.  **Personality Integration**: Giving Esther a distinct, helpful personality.
2.  **Conversational Intent Recognition**: Replacing rigid slash-commands (`/listwallets`) with flexible, natural language phrases ("show me my wallets").

This document outlines the phased approach to implementing these features, with a strong emphasis on testing at each stage to ensure stability.

## 2. Phase 1: Personality & Enhanced Introduction
**Goal**: Implement a friendly introduction and a clear way for users to discover Esther's capabilities.

**Implementation Steps**:
1.  **Update `start` command**: Modify the `start()` function in `src/main.py`.
    *   For new users, the bot will introduce itself: "Hello! I'm Esther, your AI agent for navigating the world of decentralized finance. Would you like to see what I can do?"
    *   For returning users, the "Welcome back!" message will be enhanced with the same prompt.
2.  **Update `help` command**: The existing `/help` command will be repurposed to be the main capability showcase. It will be triggered by the "what can I do?" prompt and will list the bot's core functions in a user-friendly way.

**Testing Strategy**:
*   **Unit Tests**: In `tests/test_main.py`, I will add tests to verify that the `start` command handler returns the correct welcome message for both new and returning users. I will also test the `help` command's new output.
*   **E2E Tests**: The `e2e_test.py` can be updated to check that the `/start` command on a fresh database produces the new welcome message.

## 3. Phase 2: Conversational Command Implementation
**Goal**: Enable Esther to understand and respond to natural language commands instead of just slash-commands.

**Implementation Steps (per command)**:
1.  **Update NLP Prompt**: The core prompt in `src/nlp.py` that is sent to the Gemini model will be updated. I will add instructions for it to recognize new, specific intents based on user phrases.
    *   `list_wallets`: "show my wallets", "can you list my wallets?", etc.
    *   `add_wallet`: "I want to add a new wallet", "add wallet", etc.
    *   `show_portfolio`: "what's in my portfolio?", "show me my assets", etc.
2.  **Route Intents**: In `src/main.py`, the `handle_text()` function will be updated. It will use the `intent` returned by the NLP client to call the appropriate function (e.g., if `intent == 'list_wallets'`, it will call the existing `list_wallets()` function).
3.  **Iterative Rollout**: I will implement this one command at a time, starting with "list wallets", to ensure stability.

**Testing Strategy (per command)**:
1.  **NLP Unit Test**: In `tests/test_nlp.py`, I will add tests to verify that the `NLPClient` can correctly parse a natural language phrase into the intended structured `intent` object. This will mock the call to the Gemini API.
2.  **Handler Unit Test**: In `tests/test_main.py`, I will add tests for the `handle_text` function. These tests will mock the `NLPClient` and verify that for a given intent (e.g., `{'intent': 'list_wallets'}`), the correct application logic (the `list_wallets` function) is called.
3.  **E2E Test**: In `e2e_test.py`, I will add a new test case that sends a live natural language query to the `NLPClient` to ensure the real Gemini model is parsing the intent correctly.

By following this phased, test-driven approach, we can robustly and safely evolve Esther into a much more powerful and user-friendly AI assistant. 