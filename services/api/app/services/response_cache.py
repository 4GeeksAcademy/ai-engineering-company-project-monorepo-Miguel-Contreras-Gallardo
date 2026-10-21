"""Small process-local TTL cache for read-heavy API aggregates.

This cache intentionally stores only detached response values (dicts and
Pydantic response models), never SQLAlchemy sessions or ORM instances.
"""

from copy import deepcopy
from threading import RLock
from time import monotonic
from typing import Callable, TypeVar

T = TypeVar("T")

_DEFAULT_TTL_SECONDS = 20.0
_entries: dict[str, tuple[float, object]] = {}
_lock = RLock()


def get_or_set(key: str, loader: Callable[[], T], ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> T:
    """Return a fresh cached copy, populating the entry on a miss/expiry."""
    now = monotonic()
    with _lock:
        entry = _entries.get(key)
        if entry is not None and entry[0] > now:
            return deepcopy(entry[1])
        if entry is not None:
            _entries.pop(key, None)

    value = loader()
    with _lock:
        _entries[key] = (monotonic() + ttl_seconds, deepcopy(value))
    return value


def invalidate(prefix: str) -> None:
    """Remove entries whose keys start with a domain prefix."""
    with _lock:
        for key in tuple(_entries):
            if key.startswith(prefix):
                del _entries[key]


def clear() -> None:
    """Clear all entries (used by tests and administrative maintenance)."""
    with _lock:
        _entries.clear()


def database_scope(db) -> str:
    """Keep entries from separate database engines (especially tests) isolated."""
    return str(id(db.get_bind()))


