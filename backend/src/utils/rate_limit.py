from collections import deque
from threading import Lock
from time import time


class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time()
        with self._lock:
            entries = self._hits.setdefault(key, deque())

            while entries and now - entries[0] >= self.window_seconds:
                entries.popleft()

            if len(entries) >= self.limit:
                retry_after = int(self.window_seconds - (now - entries[0])) + 1
                return False, max(retry_after, 1)

            entries.append(now)
            return True, 0


rate_limiter = InMemoryRateLimiter(limit=20, window_seconds=60)
