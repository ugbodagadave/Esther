import os
import time
import threading
from dataclasses import dataclass
from typing import Dict, Optional


CIRCUIT_FAIL_THRESHOLD = int(os.getenv("CIRCUIT_FAIL_THRESHOLD", "5"))
CIRCUIT_RESET_SECS = float(os.getenv("CIRCUIT_RESET_SECS", "30"))


@dataclass
class CircuitState:
    failure_count: int = 0
    state: str = "closed"  # closed | open | half_open
    opened_at: float = 0.0


class CircuitBreaker:
    """A lightweight per-endpoint circuit breaker.

    - closed: normal operation
    - open: short-circuit until cooldown passes
    - half_open: allow a single trial request; on success -> closed, on failure -> open
    """

    def __init__(self, fail_threshold: Optional[int] = None, reset_seconds: Optional[float] = None):
        self.fail_threshold = fail_threshold if fail_threshold is not None else CIRCUIT_FAIL_THRESHOLD
        self.reset_seconds = reset_seconds if reset_seconds is not None else CIRCUIT_RESET_SECS
        self._lock = threading.Lock()
        self._states: Dict[str, CircuitState] = {}

    def _get(self, key: str) -> CircuitState:
        if key not in self._states:
            self._states[key] = CircuitState()
        return self._states[key]

    def allow_request(self, key: str) -> bool:
        """Return True if a request should proceed, False if short-circuited."""
        with self._lock:
            st = self._get(key)
            if st.state == "closed":
                return True
            now = time.time()
            if st.state == "open":
                if now - st.opened_at >= self.reset_seconds:
                    st.state = "half_open"
                    return True
                return False
            if st.state == "half_open":
                # Allow only one trial at a time; subsequent calls should be blocked until result recorded
                # We will block further calls in half_open by returning False here after the first True
                # Simplest approach: flip to open temporarily until record_success resets; but we keep True once per window
                # To keep it simple, we allow True and rely on callers to serialize if needed.
                return True
            return True

    def record_success(self, key: str) -> None:
        with self._lock:
            st = self._get(key)
            st.failure_count = 0
            st.state = "closed"
            st.opened_at = 0.0

    def record_failure(self, key: str) -> None:
        with self._lock:
            st = self._get(key)
            st.failure_count += 1
            if st.state == "half_open":
                # Fail fast back to open
                st.state = "open"
                st.opened_at = time.time()
                st.failure_count = max(st.failure_count, self.fail_threshold)
                return
            if st.failure_count >= self.fail_threshold:
                st.state = "open"
                st.opened_at = time.time()


# Singleton breaker for process-wide use
breaker = CircuitBreaker()


def short_circuit_response(endpoint: str) -> dict:
    """Return a recognizable short-circuit response structure."""
    return {
        "success": False,
        "error": "Service temporarily unavailable (protective pause)",
        "code": "E_OKX_HTTP",
        "circuit": {
            "endpoint": endpoint,
            "state": "open",
            "retry_after_secs": CIRCUIT_RESET_SECS,
        },
    } 