import os
import random
import time
from typing import List, Callable


# Environment-configurable defaults
BACKOFF_BASE_SECS = float(os.getenv("BACKOFF_BASE_SECS", "0.2"))
BACKOFF_MULTIPLIER = float(os.getenv("BACKOFF_MULTIPLIER", "2.0"))
BACKOFF_MAX_SECS = float(os.getenv("BACKOFF_MAX_SECS", "5.0"))
# Jitter as a fraction of the computed delay (e.g., 0.1 => ±10%)
BACKOFF_JITTER_FRAC = float(os.getenv("BACKOFF_JITTER_FRAC", "0.1"))


def compute_exponential_backoff_delays(
    max_attempts: int,
    base_seconds: float | None = None,
    multiplier: float | None = None,
    max_seconds: float | None = None,
    jitter_fraction: float | None = None,
) -> List[float]:
    """Return a list of sleep durations for retries using exponential backoff with jitter.

    The list length is max_attempts - 1 because the first attempt happens immediately,
    with sleeps applied only between attempts.
    """
    if max_attempts <= 1:
        return []

    base = BACKOFF_BASE_SECS if base_seconds is None else base_seconds
    mult = BACKOFF_MULTIPLIER if multiplier is None else multiplier
    max_sleep = BACKOFF_MAX_SECS if max_seconds is None else max_seconds
    jitter_frac = BACKOFF_JITTER_FRAC if jitter_fraction is None else jitter_fraction

    delays: List[float] = []
    current = base
    for _ in range(max_attempts - 1):
        delay = min(current, max_sleep)
        if jitter_frac > 0:
            jitter = delay * jitter_frac
            delay = max(0.0, delay + random.uniform(-jitter, jitter))
        delays.append(delay)
        current *= mult
    return delays


def sleep_with_backoff(
    attempt_index: int,
    delays: List[float],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    """Sleep according to the precomputed delays for the given attempt index.

    attempt_index is 0-based. No sleep occurs if attempt_index is out of range.
    """
    if 0 <= attempt_index < len(delays):
        sleep_duration = delays[attempt_index]
        if sleep_duration > 0:
            sleep_fn(sleep_duration) 