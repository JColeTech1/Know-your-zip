"""
Pickle-based disk cache helpers for ArcGIS data.

All pickle I/O in the project goes through this module.
No other file should import pickle directly.
"""

from __future__ import annotations

import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypeVar, cast

from src.constants import CACHE_DIRECTORY, CACHE_EXPIRY_DAYS

logger = logging.getLogger(__name__)

T = TypeVar("T")


def _cache_root() -> Path:
    """Return the cache directory, creating it if necessary."""
    root = Path(CACHE_DIRECTORY)
    root.mkdir(exist_ok=True)
    return root


def cache_path(key: str) -> Path:
    """Return the .pkl file path for *key*."""
    return _cache_root() / f"{key}.pkl"


def is_cache_valid(key: str) -> bool:
    """Return True if a non-stale pickle file exists for *key*."""
    path = cache_path(key)
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(days=CACHE_EXPIRY_DAYS)


def load_pickle(key: str, expected_type: type[T]) -> T | None:
    """
    Load and return cached data for *key*.

    Returns None if the cache is missing, stale, or the stored type
    does not match *expected_type*.
    """
    if not is_cache_valid(key):
        return None
    try:
        with cache_path(key).open("rb") as fh:
            raw: object = pickle.load(fh)  # noqa: S301
        if not isinstance(raw, expected_type):
            logger.warning(
                "Cache '%s' contains %s, expected %s — discarding",
                key,
                type(raw).__name__,
                expected_type.__name__,
            )
            return None
        return cast(T, raw)
    except Exception as exc:
        logger.error("Failed to load pickle cache '%s': %s", key, exc)
        return None


def save_pickle(key: str, data: object) -> None:
    """Persist *data* to disk under *key*."""
    try:
        with cache_path(key).open("wb") as fh:
            pickle.dump(data, fh)
        logger.debug("Saved pickle cache '%s'", key)
    except Exception as exc:
        logger.error("Failed to save pickle cache '%s': %s", key, exc)
