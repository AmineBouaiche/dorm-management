from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from math import ceil
from threading import Lock
from time import monotonic


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    limit: int
    window_seconds: int


class SlidingWindowRateLimiter:
    """Small in-process sliding-window limiter for a single-worker deployment."""

    def __init__(self, max_keys: int = 10_000) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._max_keys = max_keys

    def retry_after(self, key: str, rule: RateLimitRule) -> int | None:
        now = monotonic()
        with self._lock:
            events = self._events.get(key)
            if events is None:
                return None
            self._prune(events, rule, now)
            if not events:
                self._events.pop(key, None)
                return None
            if len(events) < rule.limit:
                return None
            return max(1, ceil(rule.window_seconds - (now - events[0])))

    def record(self, key: str, rule: RateLimitRule) -> int | None:
        now = monotonic()
        with self._lock:
            events = self._events.get(key)
            if events is None:
                if len(self._events) >= self._max_keys:
                    self._evict_one_expired_or_oldest(now)
                events = self._events[key]
            self._prune(events, rule, now)
            events.append(now)
            if len(events) <= rule.limit:
                return None
            return max(1, ceil(rule.window_seconds - (now - events[0])))

    def clear(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


    def _evict_one_expired_or_oldest(self, now: float) -> None:
        for existing_key, events in list(self._events.items()):
            if not events or now - events[-1] > 60 * 60:
                self._events.pop(existing_key, None)
                return
        if self._events:
            self._events.pop(next(iter(self._events)))

    @staticmethod
    def _prune(events: deque[float], rule: RateLimitRule, now: float) -> None:
        threshold = now - rule.window_seconds
        while events and events[0] <= threshold:
            events.popleft()


AUTH_RATE_LIMITER = SlidingWindowRateLimiter()
LOGIN_IP_RULE = RateLimitRule(limit=20, window_seconds=5 * 60)
LOGIN_ACCOUNT_RULE = RateLimitRule(limit=8, window_seconds=15 * 60)
REGISTER_IP_RULE = RateLimitRule(limit=10, window_seconds=60 * 60)
