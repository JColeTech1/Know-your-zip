"""
Map Explorer tab — coordinator (≤200 lines).

Responsibilities only:
  1. Resolve user location (ZIP or address) → (lat, lon)
  2. Orchestrate data fetch via src/ui/data_fetcher.py
  3. Render map via src/ui/map_builder.py
  4. Render filter sidebar via src/ui/filters.py
"""

from __future__ import annotations

import logging
import re
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from src.api.education import EducationAPI
from src.api.emergency import EmergencyServicesAPI
from src.api.geo import GeoDataAPI
from src.api.healthcare import HealthcareAPI
from src.api.infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI
from src.constants import (
    MAP_DEFAULT_HEIGHT,
    MAP_DEFAULT_WIDTH,
    MIAMI_DEFAULT_LAT,
    MIAMI_DEFAULT_LON,
    MIAMI_DEFAULT_ZOOM,
    MIAMI_SEARCH_ZOOM,
    ZIP_CODE_PATTERN,
)
from src.ui.data_fetcher import build_geo_data, build_markers
from src.ui.filters import render_filter_sidebar
from src.ui.map_builder import add_geo_layers_to_map, add_markers_to_map, build_base_map
from src.utils.geocoder import geocode_address
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)
_ZIP_RE = re.compile(ZIP_CODE_PATTERN)


# ---------------------------------------------------------------------------
# Cached resource initialisation
# ---------------------------------------------------------------------------

@st.cache_resource
def get_apis() -> dict:
    return {
        "Education": EducationAPI(),
        "Emergency": EmergencyServicesAPI(),
        "Healthcare": HealthcareAPI(),
        "Infrastructure": {
            "Bus Stops": BusStopsAPI(),
            "Libraries": LibrariesAPI(),
            "Parks": ParksAPI(),
        },
        "GeoData": GeoDataAPI(),
    }


@st.cache_resource
def get_zip_validator() -> ZIPValidator:
    return ZIPValidator()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    defaults: dict[str, Any] = {
        "map_center": [MIAMI_DEFAULT_LAT, MIAMI_DEFAULT_LON],
        "zoom_level": MIAMI_DEFAULT_ZOOM,
        "markers": [],
        "last_location": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _resolve_location(
    location_input: str,
    zip_validator: ZIPValidator,
) -> tuple[float, float] | None:
    """Return (lat, lon) for a ZIP or free-text address, or None on failure."""
    if _ZIP_RE.match(location_input.strip()):
        is_valid, message, _ = zip_validator.validate_zip(location_input)
        if not is_valid:
            st.error(message)
            _show_valid_zips(zip_validator)
            return None
        coords = zip_validator.get_zip_coordinates(location_input)
        if not coords:
            st.error("Could not get coordinates for this ZIP code.")
            return None
        return coords

    coords = geocode_address(location_input)
    if not coords:
        st.error("Could not find coordinates for the provided location.")
    return coords


def _show_valid_zips(zip_validator: ZIPValidator) -> None:
    with st.expander("Show valid Miami-Dade County ZIP codes"):
        valid = sorted(zip_validator.get_all_zip_codes())
        cols = st.columns(5)
        for i, z in enumerate(valid):
            cols[i % 5].write(z)


def _normalise_center(center: Any) -> list[float]:
    if isinstance(center, dict):
        return [center["lat"], center["lng"]]
    return list(center)


# ---------------------------------------------------------------------------
# Main entry point (called by app.py)
# ---------------------------------------------------------------------------

def main() -> None:
    _init_session_state()
    apis = get_apis()
    zip_validator = get_zip_validator()

    st.title("🗺️ Miami-Dade County Unified Map Explorer")
    st.write("Explore infrastructure, services, and geographic data in Miami-Dade County")

    col1, col2 = st.columns([1, 2])

    with col1:
        with st.form(key="location_form", clear_on_submit=False):
            in_col, btn_col = st.columns([4, 1])
            with in_col:
                location_input = st.text_input(
                    "Enter your address or ZIP code", key="location_input"
                )
            with btn_col:
                submitted = st.form_submit_button("Enter Location")
            filters = render_filter_sidebar()

        if submitted:
            if not location_input:
                st.error("Please enter an address or ZIP code.")
            else:
                coords = _resolve_location(location_input, zip_validator)
                if coords:
                    st.session_state.map_center = list(coords)
                    st.session_state.zoom_level = MIAMI_SEARCH_ZOOM
                    st.session_state.last_location = location_input

                    with st.spinner("Fetching data…"):
                        st.session_state.markers = build_markers(
                            apis, zip_validator, coords, filters
                        )
                        geo = build_geo_data(apis["GeoData"], filters, coords)
                        if geo:
                            st.session_state.geo_data = geo
                        elif hasattr(st.session_state, "geo_data"):
                            del st.session_state.geo_data

                    st.success(
                        f"Found {len(st.session_state.markers) - 1} locations "
                        f"within {filters.radius} miles"
                    )

    with col2:
        center = _normalise_center(st.session_state.map_center)
        m = build_base_map(center, st.session_state.zoom_level)
        add_markers_to_map(m, st.session_state.markers)
        if hasattr(st.session_state, "geo_data"):
            add_geo_layers_to_map(m, st.session_state.geo_data)
        folium.LayerControl().add_to(m)

        map_data = st_folium(
            m, width=MAP_DEFAULT_WIDTH, height=MAP_DEFAULT_HEIGHT, key="main_map"
        )
        if map_data:
            if map_data.get("center"):
                st.session_state.map_center = _normalise_center(map_data["center"])
            if map_data.get("zoom"):
                st.session_state.zoom_level = map_data["zoom"]


if __name__ == "__main__":
    main()
