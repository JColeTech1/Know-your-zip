"""
GeoDataAPI — geographic overlay data for Miami-Dade County.

Provides flood zones, primary evacuation routes, and bus routes as GeoJSON
FeatureCollections for use as Folium map overlays.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.base import ArcGISError, BaseAPIClient
from src.constants import (
    MAX_FEATURES_PER_REQUEST,
    SERVICE_BUS_ROUTES,
    SERVICE_EVACUATION_ROUTES,
    SERVICE_FLOOD_ZONES,
)

logger = logging.getLogger(__name__)

_RECORD_LIMIT: dict[str, str] = {
    "resultRecordCount": str(MAX_FEATURES_PER_REQUEST),
}


class GeoDataAPI(BaseAPIClient):
    """Fetches geographic overlay data (flood zones, evacuation routes, bus routes)."""

    def get_flood_zones(self) -> dict[str, Any] | None:
        """Return FEMA flood zone polygons as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_FLOOD_ZONES, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch flood zones: %s", exc)
            return None

    def get_evacuation_routes(self) -> dict[str, Any] | None:
        """Return primary evacuation routes as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_EVACUATION_ROUTES, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch evacuation routes: %s", exc)
            return None

    def get_bus_routes(self) -> dict[str, Any] | None:
        """Return bus routes as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_BUS_ROUTES, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch bus routes: %s", exc)
            return None
