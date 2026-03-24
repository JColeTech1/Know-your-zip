"""
HealthcareAPI — hospitals, mental health centers, and clinics in Miami-Dade County.

Hospitals are fetched from the Miami-Dade opendata endpoint (full URL).
Mental health centers and clinics are fetched from the ArcGIS feature service.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.base import ArcGISError, BaseAPIClient
from src.constants import (
    MAX_FEATURES_PER_REQUEST,
    SERVICE_CLINICS,
    SERVICE_HOSPITALS,
    SERVICE_MENTAL_HEALTH,
)

logger = logging.getLogger(__name__)

_RECORD_LIMIT: dict[str, str] = {
    "resultRecordCount": str(MAX_FEATURES_PER_REQUEST),
}


class HealthcareAPI(BaseAPIClient):
    """Fetches healthcare facility records for Miami-Dade County."""

    def get_hospitals(self) -> dict[str, Any] | None:
        """Return all hospitals as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch("", full_url=SERVICE_HOSPITALS)
        except ArcGISError as exc:
            logger.error("Failed to fetch hospitals: %s", exc)
            return None

    def get_mental_health_centers(self) -> dict[str, Any] | None:
        """Return all mental health centers as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_MENTAL_HEALTH, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch mental health centers: %s", exc)
            return None

    def get_free_standing_clinics(self) -> dict[str, Any] | None:
        """Return all free-standing clinics as a GeoJSON FeatureCollection, or None on error."""
        try:
            return self.fetch(SERVICE_CLINICS, params=_RECORD_LIMIT)
        except ArcGISError as exc:
            logger.error("Failed to fetch clinics: %s", exc)
            return None
