"""
Filter sidebar and geographic data filtering.

render_filter_sidebar() renders the Streamlit checkbox/slider widgets and
returns a FilterState dataclass.  filter_geographic_data() is pure logic
with no Streamlit calls.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import streamlit as st

from src.constants import (
    DEFAULT_SEARCH_RADIUS_MILES,
    MAX_SEARCH_RADIUS_MILES,
    MIN_SEARCH_RADIUS_MILES,
    ZIP_CODE_PATTERN,
)
from src.utils.distance import miles_between
from src.utils.geocoder import geocode_address
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)

# Type alias
LatLon = tuple[float, float]

_ZIP_RE = re.compile(ZIP_CODE_PATTERN)


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


@st.cache_resource
def _get_zip_validator() -> ZIPValidator:
    """Process-level singleton so ZIP data loads only once."""
    return ZIPValidator()


def _resolve_location_input(location_input: str) -> LatLon | None:
    """Geocode a ZIP code or address → (lat, lon), or None on failure."""
    if _ZIP_RE.match(location_input):
        zv = _get_zip_validator()
        is_valid, _msg, _record = zv.validate_zip(location_input)
        if is_valid:
            return zv.get_zip_coordinates(location_input)  # returns (lat, lon) tuple
        return None
    return geocode_address(location_input)


def render_location_form() -> None:
    """
    Render a location entry form usable on any tab.

    On submit, stores resolved_coords, last_location, and location_submitted
    in session state and invalidates fetch-dedup keys so data refreshes.
    """
    with st.form(key="location_form_sidebar", clear_on_submit=False):
        in_col, btn_col = st.columns([4, 1])
        with in_col:
            location_input = st.text_input(
                "Enter your address or ZIP code",
                value=st.session_state.get("last_location", ""),
            )
        with btn_col:
            st.write("")  # vertical alignment nudge
            submitted = st.form_submit_button("Set Location")

    if submitted:
        clean = location_input.strip()
        if not clean:
            st.error("Please enter an address or ZIP code.")
            return
        coords = _resolve_location_input(clean)
        if coords:
            st.session_state.resolved_coords = coords
            st.session_state.last_location = clean
            st.session_state.location_submitted = True
            st.session_state.fetch_key = None
            st.session_state.dash_fetch_key = ""
            st.session_state.ai_context_key = None
            st.success(f"Location set: {clean}")
        else:
            st.error(
                "Location not found. Try a Miami-Dade ZIP code (e.g. 33186) "
                "or full street address."
            )


def render_filter_sidebar() -> FilterState:
    """Render category checkboxes and radius slider; return their current values."""
    st.subheader("Select Categories to Display")

    ss = st.session_state
    st.write("Education")
    show_public = st.checkbox("Public Schools", value=ss.get("filter_public_schools", True), key="filter_public_schools")
    show_private = st.checkbox("Private Schools", value=ss.get("filter_private_schools", True), key="filter_private_schools")
    show_charter = st.checkbox("Charter Schools", value=ss.get("filter_charter_schools", True), key="filter_charter_schools")

    st.write("Emergency Services")
    show_police = st.checkbox("Police Stations", value=ss.get("filter_police", True), key="filter_police")
    show_fire = st.checkbox("Fire Stations", value=ss.get("filter_fire", True), key="filter_fire")

    st.write("Healthcare")
    show_hospitals = st.checkbox("Hospitals", value=ss.get("filter_hospitals", True), key="filter_hospitals")
    show_mental = st.checkbox("Mental Health Centers", value=ss.get("filter_mental_health", True), key="filter_mental_health")
    show_clinics = st.checkbox("Free-Standing Clinics", value=ss.get("filter_clinics", True), key="filter_clinics")

    st.write("Infrastructure")
    show_bus_stops = st.checkbox("Bus Stops", value=ss.get("filter_bus_stops", True), key="filter_bus_stops")
    show_libraries = st.checkbox("Libraries", value=ss.get("filter_libraries", True), key="filter_libraries")
    show_parks = st.checkbox("Parks", value=ss.get("filter_parks", True), key="filter_parks")

    st.write("Geographic Data")
    show_flood = st.checkbox("Flood Zones", value=ss.get("filter_flood_zones", True), key="filter_flood_zones")
    show_evac = st.checkbox("Evacuation Routes", value=ss.get("filter_evacuation_routes", True), key="filter_evacuation_routes")
    show_bus_routes = st.checkbox("Bus Routes", value=ss.get("filter_bus_routes", True), key="filter_bus_routes")

    radius = st.slider(
        "Search radius (miles)",
        MIN_SEARCH_RADIUS_MILES,
        MAX_SEARCH_RADIUS_MILES,
        value=st.session_state.get("filter_radius", DEFAULT_SEARCH_RADIUS_MILES),
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
