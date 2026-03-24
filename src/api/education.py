"""
EducationAPI — public, private, and charter school data for Miami-Dade County.

All data is fetched from the Miami-Dade ArcGIS REST service and returned as
raw GeoJSON feature lists for consumption by src/ui/data_fetcher.py.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.base import ArcGISError, BaseAPIClient
from src.constants import (
    MAX_FEATURES_PER_REQUEST,
    SERVICE_CHARTER_SCHOOLS,
    SERVICE_PRIVATE_SCHOOLS,
    SERVICE_PUBLIC_SCHOOLS,
)

logger = logging.getLogger(__name__)

_PATH_MAP: dict[str, str] = {
    "public": SERVICE_PUBLIC_SCHOOLS,
    "private": SERVICE_PRIVATE_SCHOOLS,
    "charter": SERVICE_CHARTER_SCHOOLS,
}


class EducationAPI(BaseAPIClient):
    """Fetches school records grouped by school type and ZIP code."""

    def get_schools_by_zip(
        self,
        zip_code: str,
        school_type: str,
    ) -> dict[str, Any]:
        """
        Return schools of the given type within a ZIP code.

        Args:
            zip_code: 5-digit Miami-Dade ZIP code (already validated by caller).
            school_type: One of "public", "private", or "charter".

        Returns:
            {"success": True,  "data": {"schools": [GeoJSON feature dicts]}}
            {"success": False, "error": <message>}
        """
        path = _PATH_MAP.get(school_type)
        if path is None:
            return {"success": False, "error": f"Unknown school type: {school_type!r}"}

        params: dict[str, str] = {
            "where": f"ZIPCODE='{zip_code}'",
            "resultRecordCount": str(MAX_FEATURES_PER_REQUEST),
        }
        try:
            data = self.fetch(path, params=params)
            features: list[Any] = data.get("features", [])
            return {"success": True, "data": {"schools": features}}
        except ArcGISError as exc:
            logger.error(
                "Failed to fetch %s schools for ZIP %s: %s",
                school_type,
                zip_code,
                exc,
            )
            return {"success": False, "error": str(exc)}
