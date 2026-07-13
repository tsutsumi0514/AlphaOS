"""Small in-memory TTL cache helpers for AlphaOS."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: float


_CACHE: dict[str, CacheEntry[object]] = {}


def get_cached_value(key: str, producer: Callable[[], T], ttl_seconds: int) -> T:
    """Return a cached value when fresh, otherwise compute and store it."""
    now = monotonic()
    entry = _CACHE.get(key)
    if entry is not None and entry.expires_at > now:
        return entry.value  # type: ignore[return-value]

    value = producer()
    if value is not None:
        _CACHE[key] = CacheEntry(value=value, expires_at=now + ttl_seconds)
    else:
        _CACHE.pop(key, None)
    return value
