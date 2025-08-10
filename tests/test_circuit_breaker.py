import time
import unittest
from src.circuit import CircuitBreaker


class TestCircuitBreaker(unittest.TestCase):
    def test_trip_and_open_and_half_open_and_close(self):
        breaker = CircuitBreaker(fail_threshold=2, reset_seconds=0.2)
        key = "test/endpoint"

        # Initially closed, allow
        self.assertTrue(breaker.allow_request(key))

        # Record one failure; still closed
        breaker.record_failure(key)
        self.assertTrue(breaker.allow_request(key))

        # Second failure should open the circuit
        breaker.record_failure(key)
        self.assertFalse(breaker.allow_request(key))  # open -> short-circuit

        # After cooldown, it should move to half-open and allow one trial
        time.sleep(0.25)
        self.assertTrue(breaker.allow_request(key))  # half-open allow

        # On success, it should close
        breaker.record_success(key)
        self.assertTrue(breaker.allow_request(key))  # closed again

    def test_half_open_failure_goes_back_to_open(self):
        breaker = CircuitBreaker(fail_threshold=1, reset_seconds=0.1)
        key = "another/endpoint"

        # Trip to open with one failure
        breaker.record_failure(key)
        self.assertFalse(breaker.allow_request(key))

        # Wait for half-open
        time.sleep(0.12)
        self.assertTrue(breaker.allow_request(key))

        # Record a failure in half-open, should go back to open immediately
        breaker.record_failure(key)
        self.assertFalse(breaker.allow_request(key))


if __name__ == "__main__":
    unittest.main() 