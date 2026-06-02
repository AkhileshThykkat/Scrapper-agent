"""
In-memory LRU cache for analysis results and LLM responses.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Thread-safe in-memory LRU cache with TTL expiration."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 3600):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        raw = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            value, ts = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time())
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(self._hits + self._misses, 1),
        }
