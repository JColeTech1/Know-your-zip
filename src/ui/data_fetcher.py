"""
Data-fetching orchestration for the Map Explorer tab.

This module coordinates API calls and converts raw ArcGIS GeoJSON features
into the simple MarkerDict format consumed by map_builder.py.

It has NO Streamlit calls and NO direct HTTP requests.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from src.api.education import EducationAPI
from src.api.emergency import EmergencyServicesAPI
from src.api.geo import GeoDataAPI
from src.api.healthcare import HealthcareAPI
from src.api.infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI

from src.constants import MARKER_COLOR
from src.ui.filters import FilterState, filter_geographic_data
from src.ui.map_builder import (
    emergency_popup,
    healthcare_popup,
    infrastructure_popup,
    school_popup,
)
from src.utils.distance import miles_between
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)

LatLon = tuple[float, float]
MarkerDict = dict[str, Any]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_markers(
    apis: dict,
    zip_validator: ZIPValidator,
    coordinates: LatLon,
    filters: FilterState,
) -> list[MarkerDict]:
    """Return a list of MarkerDicts starting with the user-location pin."""
    markers: list[MarkerDict] = [{
        "location": list(coordinates),
        "popup": "📍 Your Location",
        "icon": MARKER_COLOR["user_location"],
        "is_user_location": True,
    }]
    nearby_zips = _nearby_zips(zip_validator, coordinates, filters.radius)

    if filters.show_public_schools or filters.show_private_schools or filters.show_charter_schools:
        markers.extend(_fetch_schools(apis["Education"], coordinates, filters, nearby_zips))
    if filters.show_police or filters.show_fire:
        markers.extend(_fetch_emergency(apis["Emergency"], coordinates, filters))
    if filters.show_hospitals or filters.show_mental_health or filters.show_clinics:
        markers.extend(_fetch_healthcare(apis["Healthcare"], coordinates, filters))
    if filters.show_bus_stops or filters.show_libraries or filters.show_parks:
        markers.extend(_fetch_infrastructure(apis["Infrastructure"], coordinates, filters))
    return markers


def build_geo_data(
    api: GeoDataAPI,
    filters: FilterState,
    coordinates: LatLon,
) -> dict[str, Any]:
    """Fetch and spatially filter geographic overlay data."""
    raw: dict[str, Any] = {}
    if filters.show_flood_zones:
        _add_if_valid(raw, api.get_flood_zones(), "flood_zones", "flood_zone_color", "blue")
    if filters.show_evacuation_routes:
        _add_if_valid(raw, api.get_evacuation_routes(), "evacuation_routes", "evacuation_route_color", "red")
    if filters.show_bus_routes:
        _add_if_valid(raw, api.get_bus_routes(), "bus_routes", "bus_route_color", "green")
    return filter_geographic_data(raw, coordinates, filters.radius) if raw else {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _nearby_zips(zip_validator: ZIPValidator, center: LatLon, radius: float) -> list[str]:
    result = []
    for z in zip_validator.get_all_zip_codes():
        zc = zip_validator.get_zip_coordinates(z)
        if zc and miles_between(center, zc) <= radius:
            result.append(z)
    return result


def _fetch_schools(
    api: EducationAPI,
    coords: LatLon,
    f: FilterState,
    zips: list[str],
) -> list[MarkerDict]:
    markers: list[MarkerDict] = []
    type_flags = [
        ("public", f.show_public_schools),
        ("private", f.show_private_schools),
        ("charter", f.show_charter_schools),
    ]
    for school_type, enabled in type_flags:
        if not enabled:
            continue
        for zip_code in zips:
            result = api.get_schools_by_zip(zip_code, school_type)
            if not result.get("success"):
                continue
            for school in result["data"].get("schools", []):
                school["school_type"] = school_type
                m = _school_marker(school, coords, f.radius, school_type)
                if m:
                    markers.append(m)
    return markers


def _school_marker(school: dict, user: LatLon, radius: float, school_type: str) -> MarkerDict | None:
    raw = (school.get("geometry") or {}).get("coordinates", [])
    if len(raw) < 2:
        return None
    pt: LatLon = (raw[1], raw[0])
    dist = miles_between(user, pt)
    if dist > radius:
        return None
    return {
        "location": list(pt),
        "popup": school_popup(school, school_type, dist),
        "icon": MARKER_COLOR.get(f"{school_type}_school", "blue"),
        "distance": dist,
    }


def _fetch_emergency(api: EmergencyServicesAPI, coords: LatLon, f: FilterState) -> list[MarkerDict]:
    markers: list[MarkerDict] = []
    if f.show_police:
        markers.extend(_feature_markers(api.get_police_stations(), coords, f.radius, "Police Station", "police", emergency_popup))
    if f.show_fire:
        markers.extend(_feature_markers(api.get_fire_stations(), coords, f.radius, "Fire Station", "fire", emergency_popup))
    return markers


def _fetch_healthcare(api: HealthcareAPI, coords: LatLon, f: FilterState) -> list[MarkerDict]:
    markers: list[MarkerDict] = []
    if f.show_hospitals:
        markers.extend(_feature_markers(api.get_hospitals(), coords, f.radius, "hospital", "hospital", healthcare_popup))
    if f.show_mental_health:
        markers.extend(_feature_markers(api.get_mental_health_centers(), coords, f.radius, "mental_health", "mental_health", healthcare_popup))
    if f.show_clinics:
        markers.extend(_feature_markers(api.get_free_standing_clinics(), coords, f.radius, "clinic", "clinic", healthcare_popup))
    return markers


def _fetch_infrastructure(api_map: dict, coords: LatLon, f: FilterState) -> list[MarkerDict]:
    markers: list[MarkerDict] = []
    if f.show_bus_stops:
        markers.extend(_feature_markers(api_map["Bus Stops"].get_all_stops(), coords, f.radius, "bus_stop", "bus_stop", infrastructure_popup))
    if f.show_libraries:
        markers.extend(_feature_markers(api_map["Libraries"].get_all_libraries(), coords, f.radius, "library", "library", infrastructure_popup))
    if f.show_parks:
        markers.extend(_feature_markers(api_map["Parks"].get_all_parks(), coords, f.radius, "park", "park", infrastructure_popup))
    return markers


def _feature_markers(
    data: dict | None,
    user: LatLon,
    radius: float,
    label: str,
    color_key: str,
    popup_fn: Callable[[dict, str, float], str],
) -> list[MarkerDict]:
    if not data or "features" not in data:
        return []
    markers: list[MarkerDict] = []
    for feature in data["features"]:
        raw = (feature.get("geometry") or {}).get("coordinates", [])
        if len(raw) < 2:
            continue
        pt: LatLon = (raw[1], raw[0])
        dist = miles_between(user, pt)
        if dist > radius:
            continue
        markers.append({
            "location": list(pt),
            "popup": popup_fn(feature.get("properties", {}), label, dist),
            "icon": MARKER_COLOR.get(color_key, "gray"),
            "distance": dist,
        })
    return markers


def _add_if_valid(target: dict, data: dict | None, key: str, color_key: str, color: str) -> None:
    if data and "features" in data:
        target[key] = data
        target[color_key] = color
