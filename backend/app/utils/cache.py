"""
In-process TTL cache.

Why in-process and not Redis?
- The deployment runs a single uvicorn worker in dev/Docker. Per-process is fine.
- For multi-worker production, a per-process cache means each worker has its
  own copy. After an invalidation, peers still serve stale data for up to TTL
  seconds. That's the trade-off; keep TTLs short for endpoints where this
  matters (e.g. reserve-status uses 10s).

Cache MISSES are cheap (one DB query). Cache HITS skip the DB entirely.
Mutating endpoints MUST call invalidate() on the relevant cache.
"""
import time
from typing import Any, Optional


class TTLCache:
    """A trivially small key-value cache with per-entry expiry.

    Do NOT cache SQLAlchemy ORM instances here — they're bound to a closed
    Session by the time the next request reads them. Cache plain values
    (dicts, tuples, dataclasses, primitives) only.
    """

    def __init__(self, ttl_seconds: float):
        self._ttl = float(ttl_seconds)
        self._entries: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.monotonic() > expiry:
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._entries[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self, key: Optional[str] = None) -> None:
        """Drop a single entry (key given) or the whole cache (key=None)."""
        if key is None:
            self._entries.clear()
        else:
            self._entries.pop(key, None)

    def __len__(self) -> int:
        return len(self._entries)
