"""
Infrastructure API — bus stops, libraries, and parks in Miami-Dade County.

Each facility type has its own class so callers can cache them independently
and so adding a new facility type requires only a new class, not modifying
existing ones.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.base import ArcGISError, BaseAPIClient
from src.constants import (
    MAX_FEATURES_PER_REQUEST,
    SERVICE_BUS_STOPS,
    SERVICE_LIBRARIES,
    SERVICE_PARKS,
)

logger = logging.getLogger(__name__)

_RECORD_LIMIT: dict[str, str] = {
    "resultRecordCount": str(MAX_FEATURES_PER_REQUEST),
}


class BusStopsAPI(BaseAPIClient):
    """Fetches bus stop records for Miami-Dade County."""

    def get_all_stops(self) -> dict[str, Any] | None:
        """Return all bus stops as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_BUS_STOPS, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch bus stops: %s", exc)
            return None


class LibrariesAPI(BaseAPIClient):
    """Fetches public library records for Miami-Dade County."""

    def get_all_libraries(self) -> dict[str, Any] | None:
        """Return all libraries as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_LIBRARIES, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch libraries: %s", exc)
            return None


class ParksAPI(BaseAPIClient):
    """Fetches park records for Miami-Dade County."""

    def get_all_parks(self) -> dict[str, Any] | None:
        """Return all parks as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_PARKS, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch parks: %s", exc)
            return None
