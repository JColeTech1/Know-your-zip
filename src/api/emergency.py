"""
EmergencyServicesAPI — police and fire stations in Miami-Dade County.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.base import ArcGISError, BaseAPIClient
from src.constants import (
    MAX_FEATURES_PER_REQUEST,
    SERVICE_FIRE,
    SERVICE_POLICE,
)

logger = logging.getLogger(__name__)

_RECORD_LIMIT: dict[str, str] = {
    "resultRecordCount": str(MAX_FEATURES_PER_REQUEST),
}


class EmergencyServicesAPI(BaseAPIClient):
    """Fetches emergency service records (police and fire) for Miami-Dade County."""

    def get_police_stations(self) -> dict[str, Any] | None:
        """Return all police stations as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_POLICE, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch police stations: %s", exc)
            return None

    def get_fire_stations(self) -> dict[str, Any] | None:
        """Return all fire stations as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_FIRE, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch fire stations: %s", exc)
            return None
