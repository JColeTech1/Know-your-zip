"""
ZIPValidator — Miami-Dade County ZIP code lookup and geometry helpers.

Fetches the canonical ZIP boundary dataset from the ArcGIS REST service
and exposes helpers used by charts.py and dashboard.py.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests
from shapely.geometry import MultiPolygon, Point, Polygon

from src.constants import (
    API_TIMEOUT_SECONDS,
    ARCGIS_BASE_URL,
    ARCGIS_QUERY_PARAMS,
    MAX_FEATURES_PER_REQUEST,
    MAX_NEAREST_ZIP_MILES,
    SERVICE_ZIP_CODES,
)
from src.utils.distance import miles_between

logger = logging.getLogger(__name__)

# Compiled once at module load
_ZIP_PATTERN = re.compile(r"^\d{5}$")

# Type alias for the internal per-ZIP record
_ZipRecord = dict[str, Any]

LatLon = tuple[float, float]


def _polygon_centroid(coordinates: list[Any]) -> LatLon:
    """Return the mean centroid of a flat or nested coordinate list."""
    lats: list[float] = []
    lons: list[float] = []
    for coord in coordinates:
        if isinstance(coord[0], list):
            for point in coord:
                lons.append(float(point[0]))
                lats.append(float(point[1]))
        else:
            lons.append(float(coord[0]))
            lats.append(float(coord[1]))
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _build_database(features: list[dict[str, Any]]) -> dict[str, _ZipRecord]:
    """Convert a GeoJSON feature list into the internal ZIP database."""
    database: dict[str, _ZipRecord] = {}
    for feature in features:
        props: dict[str, Any] = feature.get("properties") or {}
        geom: dict[str, Any] = feature.get("geometry") or {}
        if "ZIPCODE" not in props or not geom.get("coordinates"):
            continue
        zip_code = str(props["ZIPCODE"])
        coords = geom["coordinates"]
        geom_type: str = geom.get("type", "")
        try:
            if geom_type == "Polygon":
                center = _polygon_centroid(coords[0])
            elif geom_type == "Point":
                center = (float(coords[1]), float(coords[0]))
            elif geom_type == "MultiPolygon":
                center = _polygon_centroid(coords[0][0])
            else:
                logger.warning("ZIPValidator: unsupported geometry %s for ZIP %s", geom_type, zip_code)
                continue
        except Exception as exc:
            logger.error("ZIPValidator: centroid failed for ZIP %s: %s", zip_code, exc)
            continue
        database[zip_code] = {
            "zipcode": zip_code,
            "geometry": geom,
            "center": center,
            "properties": props,
        }
    return database


class ZIPValidator:
    """Miami-Dade County ZIP code lookup and geometry helper."""

    def __init__(self) -> None:
        self.zip_database: dict[str, _ZipRecord] = {}
        self._refresh_zip_database()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_zip_features(self) -> list[dict[str, Any]]:
        """Fetch raw GeoJSON features from the ArcGIS ZIP code service."""
        url = f"{ARCGIS_BASE_URL}{SERVICE_ZIP_CODES}"
        try:
            response = requests.get(
                url,
                params=dict(ARCGIS_QUERY_PARAMS),
                timeout=API_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            features: list[dict[str, Any]] = data.get("features", [])
            logger.info("ZIPValidator: fetched %d ZIP features", len(features))
            return features
        except requests.exceptions.Timeout:
            logger.error("ZIPValidator: request timed out fetching ZIP codes")
        except requests.exceptions.HTTPError as exc:
            logger.error("ZIPValidator: HTTP error fetching ZIP codes: %s", exc)
        except requests.exceptions.RequestException as exc:
            logger.error("ZIPValidator: request error fetching ZIP codes: %s", exc)
        except ValueError as exc:
            logger.error("ZIPValidator: JSON decode error fetching ZIP codes: %s", exc)
        return []

    def _refresh_zip_database(self) -> None:
        """Populate the internal ZIP database from the ArcGIS service."""
        features = self._fetch_zip_features()
        self.zip_database = _build_database(features)
        logger.info("ZIPValidator: database ready, %d ZIPs loaded", len(self.zip_database))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def validate_format(self, zip_code: str) -> bool:
        """Return True if *zip_code* matches the 5-digit pattern."""
        return bool(_ZIP_PATTERN.match(zip_code))

    def get_zip_info(self, zip_code: str) -> _ZipRecord | None:
        """Return the internal record for *zip_code*, or None if not found."""
        if not self.validate_format(zip_code):
            return None
        return self.zip_database.get(zip_code)

    def get_zip_coordinates(self, zip_code: str) -> LatLon | None:
        """Return (lat, lon) centroid for *zip_code*, or None."""
        record = self.get_zip_info(zip_code)
        if record:
            center: LatLon = record["center"]
            return center
        return None

    def get_all_zip_codes(self) -> set[str]:
        """Return all loaded Miami-Dade ZIP codes."""
        return set(self.zip_database.keys())

    def get_nearby_zips(self, zip_code: str, radius_miles: float = 5.0) -> list[str]:
        """Return ZIP codes whose centroids are within *radius_miles* of *zip_code*."""
        if not self.validate_format(zip_code) or zip_code not in self.zip_database:
            return []
        center: LatLon = self.zip_database[zip_code]["center"]
        nearby: list[str] = []
        for other_zip, record in self.zip_database.items():
            if other_zip != zip_code:
                if miles_between(center, record["center"]) <= radius_miles:
                    nearby.append(other_zip)
        return nearby

    def validate_zip(self, zip_code: str) -> tuple[bool, str, _ZipRecord | None]:
        """
        Full validation of a ZIP code.

        Returns:
            (is_valid, message, info_or_None)
        """
        if not self.validate_format(zip_code):
            return False, "Invalid ZIP code format. Must be 5 digits.", None
        record = self.get_zip_info(zip_code)
        if record is None:
            return False, "ZIP code not found in Miami-Dade County.", None
        return True, "Valid Miami-Dade County ZIP code.", record

    def get_zip_area(self, zip_code: str) -> float:
        """
        Approximate area of a ZIP code in square miles.

        Returns 1.0 if the geometry is unavailable or the calculation fails.
        """
        record = self.get_zip_info(zip_code)
        if not record or "geometry" not in record:
            return 1.0
        geom: dict[str, Any] = record["geometry"]
        try:
            if geom["type"] == "Polygon":
                polygon = Polygon(geom["coordinates"][0])
                return float(polygon.area * 4000)
            if geom["type"] == "MultiPolygon":
                total = sum(
                    Polygon(ring[0]).area
                    for ring in geom["coordinates"][:MAX_FEATURES_PER_REQUEST]
                )
                return float(total * 4000)
        except Exception as exc:
            logger.error("ZIPValidator: area calculation failed for ZIP %s: %s", zip_code, exc)
        return 1.0

    def is_point_in_zip(self, lat: float, lon: float, zip_code: str) -> bool:
        """Return True if (lat, lon) falls within *zip_code* boundaries."""
        record = self.get_zip_info(zip_code)
        if not record or "geometry" not in record:
            return False
        point = Point(lon, lat)
        geom: dict[str, Any] = record["geometry"]
        try:
            if geom["type"] == "Polygon":
                return bool(Polygon(geom["coordinates"][0]).contains(point))
            if geom["type"] == "MultiPolygon":
                for ring in geom["coordinates"]:
                    if Polygon(ring[0]).contains(point):
                        return True
        except Exception as exc:
            logger.error("ZIPValidator: point-in-zip failed for %s: %s", zip_code, exc)
        return False

    def get_closest_zip(self, coordinates: LatLon) -> str | None:
        """
        Return the ZIP code whose centroid is nearest to *coordinates*.

        Returns None if no ZIP is found within MAX_NEAREST_ZIP_MILES.
        """
        closest_zip: str | None = None
        min_distance = float("inf")
        for zip_code, record in self.zip_database.items():
            try:
                distance = miles_between(coordinates, record["center"])
            except Exception as exc:
                logger.warning("ZIPValidator: distance calc failed for ZIP %s: %s", zip_code, exc)
                continue
            if distance < min_distance:
                min_distance = distance
                closest_zip = zip_code
        if closest_zip and min_distance <= MAX_NEAREST_ZIP_MILES:
            return closest_zip
        logger.warning(
            "ZIPValidator: no ZIP within %.1f miles of %s (closest was %.2f mi)",
            MAX_NEAREST_ZIP_MILES,
            coordinates,
            min_distance,
        )
        return None

    def get_zip_geojson(self) -> dict[str, Any]:
        """Return a GeoJSON FeatureCollection of all loaded ZIP boundaries."""
        features = [
            {
                "type": "Feature",
                "properties": {"ZIP_Code": zip_code},
                "geometry": record["geometry"],
            }
            for zip_code, record in self.zip_database.items()
            if "geometry" in record
        ]
        return {"type": "FeatureCollection", "features": features}
