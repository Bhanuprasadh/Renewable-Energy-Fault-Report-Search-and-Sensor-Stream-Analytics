"""Thread-safe LRU and TTL Query Cache for high-throughput search and range analytics."""
from __future__ import annotations

import collections
import threading
import time
from typing import Any, Dict, Optional, Tuple


class LRUTTLCache:
    """Least Recently Used (LRU) cache with Time-To-Live (TTL) expiration and hit/miss telemetry."""

    def __init__(self, capacity: int = 512, ttl_seconds: int = 300):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._cache: collections.OrderedDict[str, Tuple[Any, float]] = collections.OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            val, exp_time = self._cache[key]
            now = time.time()
            if now > exp_time:
                # Expired
                del self._cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.hits += 1
            return val

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            now = time.time()
            exp_time = now + self.ttl_seconds

            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.capacity:
                # Evict oldest
                self._cache.popitem(last=False)

            self._cache[key] = (value, exp_time)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def get_telemetry(self) -> Dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "capacity": self.capacity,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": round(hit_rate * 100.0, 2)
            }

