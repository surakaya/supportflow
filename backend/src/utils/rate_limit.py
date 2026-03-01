import logging
import os
import time
from collections import deque
from threading import Lock

import redis


class InMemoryRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            entries = self._hits.setdefault(key, deque())

            while entries and now - entries[0] >= self.window_seconds:
                entries.popleft()

            if len(entries) >= self.limit:
                retry_after = int(self.window_seconds - (now - entries[0])) + 1
                return False, max(retry_after, 1)

            entries.append(now)
            return True, 0


class RedisRateLimiter:
    def __init__(self, redis_url: str, limit: int = 20, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._logger = logging.getLogger(__name__)

    def check(self, key: str) -> tuple[bool, int]:
        now = int(time.time())
        bucket = now // self.window_seconds
        redis_key = f"rate_limit:{key}:{bucket}"

        try:
            with self.redis.pipeline() as pipe:
                pipe.incr(redis_key, 1)
                pipe.expire(redis_key, self.window_seconds + 1)
                current_count, _ = pipe.execute()
        except redis.RedisError as exc:
            raise RuntimeError(f"Redis rate limit check failed: {exc}") from exc

        if int(current_count) <= self.limit:
            return True, 0

        retry_after = self.window_seconds - (now % self.window_seconds)
        return False, max(retry_after, 1)


def build_rate_limiter():
    limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    redis_url = os.getenv("REDIS_URL", "").strip()

    if redis_url:
        try:
            limiter = RedisRateLimiter(
                redis_url=redis_url,
                limit=limit,
                window_seconds=window_seconds,
            )
            limiter.redis.ping()
            return limiter
        except redis.RedisError:
            logging.getLogger(__name__).warning(
                "Redis is configured but unavailable. Falling back to in-memory rate limiter."
            )

    return InMemoryRateLimiter(limit=limit, window_seconds=window_seconds)


rate_limiter = build_rate_limiter()
