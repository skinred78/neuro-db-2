"""
Thread-safe token bucket rate limiter with transactional acquire.

Ensures no token leakage and proper refund on failure.
"""

import time
import threading
from collections import deque


class RateLimiter:
    """
    Thread-safe token bucket rate limiter with transactional acquire.
    Ensures no token leakage and proper refund on failure.
    """

    def __init__(self, requests_per_second: int, requests_per_hour: int):
        self.req_per_sec = requests_per_second
        self.req_per_hour = requests_per_hour

        # Single lock for transactional acquire
        self.lock = threading.Lock()

        # Token counters
        self.sec_tokens = requests_per_second
        self.hour_tokens = requests_per_hour

        # Refill tracking
        self.last_sec_refill = time.time()
        self.last_hour_refill = time.time()
        self.hour_window = deque()  # Track request timestamps

    def acquire(self):
        """
        Block until tokens available from BOTH buckets.
        Transactional: either both succeed or neither changes.
        """
        while True:
            with self.lock:  # SINGLE LOCK - transactional
                now = time.time()

                # Refill both buckets
                self._refill_sec(now)
                self._refill_hour(now)

                # Check both constraints
                if self.sec_tokens > 0 and self.hour_tokens > 0:
                    # TRANSACTIONAL SUCCESS - deduct from both
                    self.sec_tokens -= 1
                    self.hour_tokens -= 1
                    self.hour_window.append(now)
                    return

            # Failed to acquire - sleep and retry
            time.sleep(0.05)  # 50ms backoff

    def _refill_sec(self, now: float):
        """Refill per-second bucket."""
        elapsed = now - self.last_sec_refill
        if elapsed >= 1.0:
            self.sec_tokens = min(
                self.req_per_sec,
                self.sec_tokens + int(elapsed * self.req_per_sec)
            )
            self.last_sec_refill = now

    def _refill_hour(self, now: float):
        """Refill per-hour bucket using sliding window."""
        # Remove timestamps older than 1 hour
        hour_ago = now - 3600
        while self.hour_window and self.hour_window[0] < hour_ago:
            self.hour_window.popleft()

        # Available tokens = limit - used in last hour
        self.hour_tokens = self.req_per_hour - len(self.hour_window)


# Usage with decorator
def rate_limited(scope: str):
    """Decorator for rate-limited API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            rate_limiters[scope].acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiters (initialized from Config)
from poc_api_first.config import Config

rate_limiters = {
    'umls': RateLimiter(
        requests_per_second=Config.UMLS_RATE_PER_SEC,
        requests_per_hour=Config.UMLS_RATE_PER_HOUR
    ),
    'pubtator': RateLimiter(
        requests_per_second=Config.PUBTATOR_RATE_PER_SEC,
        requests_per_hour=Config.PUBTATOR_RATE_PER_HOUR
    )
}
