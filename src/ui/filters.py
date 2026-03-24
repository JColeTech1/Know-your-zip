"""
Filter sidebar and geographic data filtering.

render_filter_sidebar() renders the Streamlit checkbox/slider widgets and
returns a FilterState dataclass.  filter_geographic_data() is pure logic
with no Streamlit calls.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import streamlit as st

from src.constants import (
    DEFAULT_SEARCH_RADIUS_MILES,
    MAX_SEARCH_RADIUS_MILES,
    MIN_SEARCH_RADIUS_MILES,
)
from src.utils.distance import miles_between

logger = logging.getLogger(__name__)

# Type alias
LatLon = tuple[float, float]


@dataclass
class FilterState:
    """All checkbox and slider values from the filter sidebar."""

    show_public_schools: bool
    show_private_schools: bool
    show_charter_schools: bool
    show_police: bool
    show_fire: bool
    show_hospitals: bool
    show_mental_health: bool
    show_clinics: bool
    show_bus_stops: bool
    show_libraries: bool
    show_parks: bool
    show_flood_zones: bool
    show_evacuation_routes: bool
    show_bus_routes: bool
    radius: float


def render_filter_sidebar() -> FilterState:
    """Render category checkboxes and radius slider; return their current values."""
    st.subheader("Select Categories to Display")

    st.write("Education")
    show_public = st.checkbox("Public Schools", key="filter_public_schools")
    show_private = st.checkbox("Private Schools", key="filter_private_schools")
    show_charter = st.checkbox("Charter Schools", key="filter_charter_schools")

    st.write("Emergency Services")
    show_police = st.checkbox("Police Stations", key="filter_police")
    show_fire = st.checkbox("Fire Stations", key="filter_fire")

    st.write("Healthcare")
    show_hospitals = st.checkbox("Hospitals", key="filter_hospitals")
    show_mental = st.checkbox("Mental Health Centers", key="filter_mental_health")
    show_clinics = st.checkbox("Free-Standing Clinics", key="filter_clinics")

    st.write("Infrastructure")
    show_bus_stops = st.checkbox("Bus Stops", key="filter_bus_stops")
    show_libraries = st.checkbox("Libraries", key="filter_libraries")
    show_parks = st.checkbox("Parks", key="filter_parks")

    st.write("Geographic Data")
    show_flood = st.checkbox("Flood Zones", key="filter_flood_zones")
    show_evac = st.checkbox("Evacuation Routes", key="filter_evacuation_routes")
    show_bus_routes = st.checkbox("Bus Routes", key="filter_bus_routes")

    radius = st.slider(
        "Search radius (miles)",
        MIN_SEARCH_RADIUS_MILES,
        MAX_SEARCH_RADIUS_MILES,
        key="filter_radius",
    )

    return FilterState(
        show_public_schools=show_public,
        show_private_schools=show_private,
        show_charter_schools=show_charter,
        show_police=show_police,
        show_fire=show_fire,
        show_hospitals=show_hospitals,
        show_mental_health=show_mental,
        show_clinics=show_clinics,
        show_bus_stops=show_bus_stops,
        show_libraries=show_libraries,
        show_parks=show_parks,
        show_flood_zones=show_flood,
        show_evacuation_routes=show_evac,
        show_bus_routes=show_bus_routes,
        radius=radius,
    )


def filter_geographic_data(
    geo_data: dict[str, Any],
    user_coords: LatLon,
    radius: float,
) -> dict[str, Any]:
    """
    Return a copy of geo_data containing only features within *radius* miles.

    Handles flood zones (polygons), evacuation routes, and bus routes (polylines).
    """
    filtered: dict[str, Any] = {}

    if "flood_zones" in geo_data:
        zones = _filter_polygon_features(
            geo_data["flood_zones"]["features"], user_coords, radius
        )
        if zones:
            filtered["flood_zones"] = {"type": "FeatureCollection", "features": zones}
            filtered["flood_zone_color"] = geo_data["flood_zone_color"]

    if "evacuation_routes" in geo_data:
        routes = _filter_line_features(
            geo_data["evacuation_routes"]["features"], user_coords, radius
        )
        if routes:
            filtered["evacuation_routes"] = {"type": "FeatureCollection", "features": routes}
            filtered["evacuation_route_color"] = geo_data["evacuation_route_color"]

    if "bus_routes" in geo_data:
        routes = _filter_line_features(
            geo_data["bus_routes"]["features"], user_coords, radius
        )
        if routes:
            filtered["bus_routes"] = {"type": "FeatureCollection", "features": routes}
            filtered["bus_route_color"] = geo_data["bus_route_color"]

    return filtered


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _filter_polygon_features(
    features: list[dict[str, Any]],
    user_coords: LatLon,
    radius: float,
) -> list[dict[str, Any]]:
    result = []
    for feature in features:
        try:
            geom = feature.get("geometry")
            if not geom:
                continue
            ring = geom["coordinates"][0]  # first ring of polygon
            if _any_coord_within(ring, user_coords, radius):
                result.append(feature)
        except (KeyError, IndexError, TypeError) as exc:
            logger.debug("Skipping polygon feature: %s", exc)
    return result


def _filter_line_features(
    features: list[dict[str, Any]],
    user_coords: LatLon,
    radius: float,
) -> list[dict[str, Any]]:
    result = []
    for feature in features:
        try:
            geom = feature.get("geometry")
            if not geom:
                continue
            coords = geom["coordinates"]
            # Handle MultiLineString (list of lists of coordinates)
            if coords and isinstance(coords[0][0], list):
                coords = [c for sublist in coords for c in sublist]
            if _any_coord_within(coords, user_coords, radius):
                result.append(feature)
        except (KeyError, IndexError, TypeError) as exc:
            logger.debug("Skipping line feature: %s", exc)
    return result


def _any_coord_within(
    coords: list[list[float]],
    user_coords: LatLon,
    radius: float,
) -> bool:
    for coord in coords:
        if miles_between(user_coords, (coord[1], coord[0])) <= radius:
            return True
    return False
