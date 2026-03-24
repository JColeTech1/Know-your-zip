"""
Map builder — Folium marker and layer construction.

This module only builds Folium map objects from already-validated data.
It has NO Streamlit calls and does NOT perform API requests.
"""

from __future__ import annotations

import logging
from typing import Any

import folium

from src.constants import (
    LAYER_BUS_ROUTE_OPACITY,
    LAYER_BUS_ROUTE_WEIGHT,
    LAYER_EVACUATION_OPACITY,
    LAYER_EVACUATION_WEIGHT,
    LAYER_FLOOD_FILL_OPACITY,
    LAYER_FLOOD_WEIGHT,
    MAP_DEFAULT_HEIGHT,
    MAP_DEFAULT_WIDTH,
    MAP_POPUP_MAX_WIDTH,
    MARKER_COLOR,
    MIAMI_DEFAULT_LAT,
    MIAMI_DEFAULT_LON,
    MIAMI_DEFAULT_ZOOM,
)

logger = logging.getLogger(__name__)

# Type alias for a serialised marker dict stored in session state
MarkerDict = dict[str, Any]

_TOOLTIP_STYLE = (
    "background-color: white; color: #333333; "
    "font-family: arial; font-size: 12px; padding: 10px;"
)


# ---------------------------------------------------------------------------
# Marker pop-up builders (one per facility domain)
# ---------------------------------------------------------------------------

def school_popup(properties: dict[str, Any], school_type: str, distance: float) -> str:
    return (
        f"<b>{school_type.title()} School:</b> {properties.get('NAME', 'Unknown')}<br>"
        f"Address: {properties.get('ADDRESS', 'N/A')}<br>"
        f"Grades: {properties.get('GRDLEVEL', 'N/A')}<br>"
        f"Enrollment: {properties.get('ENROLLMENT', 'N/A')}<br>"
        f"Distance: {distance:.1f} miles"
    )


def emergency_popup(properties: dict[str, Any], service_type: str, distance: float) -> str:
    return (
        f"<b>{service_type}:</b> {properties.get('NAME', 'Unknown')}<br>"
        f"Address: {properties.get('ADDRESS', 'N/A')}<br>"
        f"Phone: {properties.get('PHONE', 'N/A')}<br>"
        f"Distance: {distance:.1f} miles"
    )


def healthcare_popup(
    properties: dict[str, Any],
    facility_type: str,
    distance: float,
) -> str:
    name = _first_nonempty(properties, "NAME", "name", "FACILITY_NAME") or "Unknown"
    address = _first_nonempty(properties, "ADDRESS", "address", "STREET_ADDRESS") or "N/A"
    phone = _first_nonempty(properties, "PHONE", "phone", "PHONE_NUMBER") or "N/A"

    extra = ""
    if facility_type == "hospital":
        beds = _first_nonempty(properties, "BEDS", "NUM_BEDS") or "N/A"
        extra = f"Number of Beds: {beds}<br>"
    elif facility_type == "mental_health":
        svcs = _first_nonempty(properties, "SERVICES", "SERVICE_TYPE") or "N/A"
        extra = f"Services: {svcs}<br>"
    elif facility_type == "clinic":
        hours = _first_nonempty(properties, "HOURS", "OPERATING_HOURS") or "N/A"
        extra = f"Hours: {hours}<br>"

    return (
        f"<b>{facility_type.title()}:</b> {name}<br>"
        f"Address: {address}<br>"
        f"Phone: {phone}<br>"
        f"{extra}"
        f"Distance: {distance:.1f} miles"
    )


def infrastructure_popup(
    properties: dict[str, Any],
    facility_type: str,
    distance: float,
) -> str:
    name = _first_nonempty(properties, "NAME", "name", "FACILITY_NAME") or "Unknown"
    address = _first_nonempty(properties, "ADDRESS", "address", "STREET_ADDRESS") or "N/A"

    extra = ""
    if facility_type == "bus_stop":
        route = _first_nonempty(properties, "ROUTE", "route", "BUS_ROUTE") or "N/A"
        extra = f"Route: {route}<br>"
    elif facility_type == "library":
        hours = _first_nonempty(properties, "HOURS", "hours", "OPERATING_HOURS") or "N/A"
        phone = _first_nonempty(properties, "PHONE", "phone", "PHONE_NUMBER") or "N/A"
        extra = f"Hours: {hours}<br>Phone: {phone}<br>"
    elif facility_type == "park":
        amenities = _first_nonempty(properties, "AMENITIES", "amenities", "FACILITIES") or "N/A"
        extra = f"Amenities: {amenities}<br>"

    return (
        f"<b>{facility_type.replace('_', ' ').title()}:</b> {name}<br>"
        f"Address: {address}<br>"
        f"{extra}"
        f"Distance: {distance:.1f} miles"
    )


# ---------------------------------------------------------------------------
# Map rendering
# ---------------------------------------------------------------------------

def build_base_map(center: list[float], zoom: int) -> folium.Map:
    return folium.Map(location=center, zoom_start=zoom)


def add_markers_to_map(m: folium.Map, markers: list[MarkerDict]) -> None:
    """Add all session-state markers to a Folium map in-place."""
    for marker in markers:
        popup = folium.Popup(marker["popup"], max_width=MAP_POPUP_MAX_WIDTH)
        if marker.get("is_user_location"):
            folium.Marker(
                marker["location"],
                popup=popup,
                icon=folium.Icon(color=marker["icon"], icon="home", prefix="fa"),
            ).add_to(m)
        else:
            folium.Marker(
                marker["location"],
                popup=popup,
                icon=folium.Icon(color=marker["icon"], icon="info-sign"),
            ).add_to(m)


def add_geo_layers_to_map(m: folium.Map, geo_data: dict[str, Any]) -> None:
    """Add flood zone, evacuation route, and bus route GeoJSON layers."""
    if "flood_zones" in geo_data:
        color = geo_data["flood_zone_color"]
        folium.GeoJson(
            geo_data["flood_zones"],
            name="Flood Zones",
            style_function=lambda _: {
                "fillColor": color,
                "color": color,
                "weight": LAYER_FLOOD_WEIGHT,
                "fillOpacity": LAYER_FLOOD_FILL_OPACITY,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["ZONESUBTY", "FZONE", "ELEV"],
                aliases=["Zone Subtype:", "Flood Zone:", "Elevation:"],
                style=_TOOLTIP_STYLE,
            ),
        ).add_to(m)

    if "evacuation_routes" in geo_data:
        color = geo_data["evacuation_route_color"]
        folium.GeoJson(
            geo_data["evacuation_routes"],
            name="Evacuation Routes",
            style_function=lambda _: {
                "color": color,
                "weight": LAYER_EVACUATION_WEIGHT,
                "opacity": LAYER_EVACUATION_OPACITY,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["SN", "CREATEDBY"],
                aliases=["Serial Number:", "Created By:"],
                style=_TOOLTIP_STYLE,
            ),
        ).add_to(m)

    if "bus_routes" in geo_data:
        color = geo_data["bus_route_color"]
        folium.GeoJson(
            geo_data["bus_routes"],
            name="Bus Routes",
            style_function=lambda _: {
                "color": color,
                "weight": LAYER_BUS_ROUTE_WEIGHT,
                "opacity": LAYER_BUS_ROUTE_OPACITY,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["LINEABBR", "LINENAME", "RTNAME"],
                aliases=["Line:", "Line Name:", "Route Name:"],
                style=_TOOLTIP_STYLE,
            ),
        ).add_to(m)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _first_nonempty(d: dict[str, Any], *keys: str) -> str | None:
    """Return the first non-empty string value for any of the given keys."""
    for key in keys:
        val = d.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None
