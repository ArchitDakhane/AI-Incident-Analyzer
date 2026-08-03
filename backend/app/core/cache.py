"""Redis-backed caching helpers for the application."""

from __future__ import annotations

import json
import time
from typing import Any, Iterable

import redis
from redis.exceptions import RedisError

from app.core.config import settings


class InMemoryCache:
    """Small Redis-like fallback store used when Redis is not available."""

    def __init__(self) -> None:
        self.store: dict[str, tuple[str, float | None]] = {}

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired_keys = [
            key for key, (_, expires_at) in self.store.items() if expires_at and expires_at <= now
        ]
        for key in expired_keys:
            self.store.pop(key, None)

    def get(self, key: str) -> str | None:
        self._purge_expired()
        item = self.store.get(key)
        if item is None:
            return None
        value, _ = item
        return value

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else None
        self.store[key] = (value, expires_at)

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.store.pop(key, None)

    def scan_iter(self, match: str) -> Iterable[str]:
        self._purge_expired()
        if not match.endswith("*"):
            return [key for key in self.store if key == match]
        prefix = match[:-1]
        return [key for key in self.store if key.startswith(prefix)]

    def incr(self, key: str) -> int:
        self._purge_expired()
        current_value = self.get(key)
        next_value = int(current_value or 0) + 1
        _, expires_at = self.store.get(key, ("0", None))
        self.store[key] = (str(next_value), expires_at)
        return next_value

    def expire(self, key: str, ttl_seconds: int) -> None:
        if key not in self.store:
            return
        value, _ = self.store[key]
        self.store[key] = (value, time.monotonic() + ttl_seconds)


class CacheService:
    """Redis wrapper used for AI analysis, dashboard stats, and rate limits."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self.fallback = InMemoryCache()
        self.client = redis_client or self._build_client()

    def _build_client(self) -> Any:
        try:
            client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            return client
        except RedisError:
            return InMemoryCache()

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key."""
        try:
            value = self.client.get(key)
        except RedisError:
            self.client = self.fallback
            value = self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store a value in Redis with an expiration."""
        payload = json.dumps(value) if not isinstance(value, str) else value
        try:
            self.client.setex(key, ttl_seconds, payload)
        except RedisError:
            self.client = self.fallback
            self.client.setex(key, ttl_seconds, payload)

    def delete(self, *keys: str) -> None:
        """Remove one or more keys from the cache."""
        if keys:
            try:
                self.client.delete(*keys)
            except RedisError:
                self.client = self.fallback
                self.client.delete(*keys)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove every key that starts with the given prefix."""
        try:
            keys = list(self.client.scan_iter(match=f"{prefix}*"))
            if keys:
                self.client.delete(*keys)
        except RedisError:
            self.client = self.fallback
            keys = list(self.client.scan_iter(match=f"{prefix}*"))
            if keys:
                self.client.delete(*keys)

    def increment(self, key: str, ttl_seconds: int) -> int:
        """Atomically increment a cached counter and set a TTL on first use."""
        try:
            count = int(self.client.incr(key))
            if count == 1:
                self.client.expire(key, ttl_seconds)
            return count
        except RedisError:
            self.client = self.fallback
            count = int(self.client.incr(key))
            if count == 1:
                self.client.expire(key, ttl_seconds)
            return count


cache_service = CacheService()
