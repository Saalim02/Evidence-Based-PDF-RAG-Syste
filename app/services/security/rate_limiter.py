import time
from collections import defaultdict
from threading import Lock


# Maximum requests allowed during the configured window.
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SECONDS = 60


class RateLimiter:
    """
    Simple in-memory fixed-window rate limiter.

    This protects a single backend instance from request abuse.
    For a multi-instance deployment, this should be replaced
    with a shared store such as Redis.
    """

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_id: str) -> bool:
        now = time.monotonic()

        with self._lock:
            timestamps = self._requests[client_id]

            cutoff = now - self.window_seconds

            self._requests[client_id] = [
                timestamp
                for timestamp in timestamps
                if timestamp > cutoff
            ]

            timestamps = self._requests[client_id]

            if len(timestamps) >= self.max_requests:
                return False

            timestamps.append(now)
            return True

    def reset(self) -> None:
        """Clear all tracked clients. Useful for tests."""
        with self._lock:
            self._requests.clear()


rate_limiter = RateLimiter()
