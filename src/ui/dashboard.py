"""
Dashboard tab — county-wide overview charts + local area analysis.

UI only: renders Streamlit widgets and Plotly charts.
All API calls go through private _fetch_* helpers.
No UI code lives in api/ files; no API calls live in render helpers.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.charts import (
    plot_fire_station_proximity_pie,
    plot_schools_histogram,
    plot_zip_park_density_treemap,
)

from src.api.education import EducationAPI
from src.api.emergency import EmergencyServicesAPI
from src.api.geo import GeoDataAPI
from src.api.healthcare import HealthcareAPI
from src.api.infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI
from src.constants import (
    CHART_COLOR_SEQUENCE,
    COVERAGE_DIVISOR_EMERGENCY,
    COVERAGE_DIVISOR_HEALTHCARE,
    COVERAGE_DIVISOR_INFRASTRUCTURE,
    COVERAGE_DIVISOR_SCHOOLS,
    COVERAGE_SCORE_MAX,
    MAX_FEATURES_PER_REQUEST,
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_MEDIUM,
    RISK_WEIGHT_EMERGENCY,
    RISK_WEIGHT_FLOOD,
    RISK_WEIGHT_HEALTHCARE,
    RISK_WEIGHT_INFRASTRUCTURE,
)
from src.ui.filters import FilterState, render_filter_sidebar
from src.utils.distance import is_within_radius
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

LatLon = tuple[float, float]
NearbyData = dict[str, Any]


# ---------------------------------------------------------------------------
# API singletons (cached for the lifetime of the Streamlit process)
# ---------------------------------------------------------------------------


@st.cache_resource
def _get_apis() -> dict[str, Any]:
    return {
        "Education": EducationAPI(),
        "Healthcare": HealthcareAPI(),
        "Emergency": EmergencyServicesAPI(),
        "GeoData": GeoDataAPI(),
        "Bus Stops": BusStopsAPI(),
        "Libraries": LibrariesAPI(),
        "Parks": ParksAPI(),
    }


@st.cache_resource
def _get_zip_validator() -> ZIPValidator:
    return ZIPValidator()


# ---------------------------------------------------------------------------
# Fetch deduplication helpers
# ---------------------------------------------------------------------------


def _filters_hash(filters: FilterState) -> str:
    """Return a stable string key from all boolean filter flags."""
    flags = (
        filters.show_public_schools,
        filters.show_private_schools,
        filters.show_charter_schools,
        filters.show_police,
        filters.show_fire,
        filters.show_hospitals,
        filters.show_mental_health,
        filters.show_clinics,
        filters.show_bus_stops,
        filters.show_libraries,
        filters.show_parks,
        filters.show_flood_zones,
        filters.show_evacuation_routes,
        filters.show_bus_routes,
    )
    return "|".join(str(int(f)) for f in flags)


def _get_or_fetch(location_label: str, coords: LatLon, filters: FilterState) -> NearbyData:
    """Return cached NearbyData if key is unchanged, otherwise fetch fresh."""
    new_key = f"{location_label}|{filters.radius}|{_filters_hash(filters)}"
    if (
        st.session_state.get("dash_fetch_key") == new_key
        and st.session_state.get("dash_data") is not None
    ):
        cached: NearbyData = st.session_state["dash_data"]
        return cached
    with st.spinner("Fetching nearby data…"):
        data = _fetch_nearby_data(coords, filters)
    st.session_state["dash_data"] = data
    st.session_state["dash_fetch_key"] = new_key
    return data


# ---------------------------------------------------------------------------
# Data-fetching helpers (no Streamlit calls allowed here)
# ---------------------------------------------------------------------------


def _fetch_point_features(
    api_call: Any, label: str, coords: LatLon, radius: float
) -> list[dict[str, Any]]:
    """Return point GeoJSON features within *radius* miles, tagged with *label*."""
    items: list[dict[str, Any]] = []
    data: dict[str, Any] = api_call() or {}
    for feature in data.get("features", [])[:MAX_FEATURES_PER_REQUEST]:
        geom = feature.get("geometry") or {}
        raw = geom.get("coordinates", [])
        if len(raw) < 2:
            continue
        if is_within_radius(coords, (raw[1], raw[0]), radius):
            feature["properties"]["type"] = label
            items.append(feature)
    return items


def _fetch_schools(
    nearby_zips: list[str], filters: FilterState
) -> list[dict[str, Any]]:
    """Fetch schools for all nearby ZIP codes according to filter flags."""
    apis = _get_apis()
    schools: list[dict[str, Any]] = []
    type_flags = [
        ("public", filters.show_public_schools),
        ("private", filters.show_private_schools),
        ("charter", filters.show_charter_schools),
    ]
    for school_type, enabled in type_flags:
        if not enabled:
            continue
        for zip_code in nearby_zips[:MAX_FEATURES_PER_REQUEST]:
            result = apis["Education"].get_schools_by_zip(zip_code, school_type)
            if result and result.get("success"):
                for s in result["data"].get("schools", []):
                    s["school_type"] = school_type
                    schools.append(s)
    return schools


def _fetch_flood_zones(coords: LatLon, radius: float) -> list[dict[str, Any]]:
    apis = _get_apis()
    zones: list[dict[str, Any]] = []
    data: dict[str, Any] = apis["GeoData"].get_flood_zones() or {}
    for zone in data.get("features", [])[:MAX_FEATURES_PER_REQUEST]:
        geom = zone.get("geometry") or {}
        ring: list[list[float]] = geom.get("coordinates", [[]])[0]
        for coord in ring[:MAX_FEATURES_PER_REQUEST]:
            if is_within_radius(coords, (coord[1], coord[0]), radius):
                zones.append(zone)
                break
    return zones


def _fetch_emergency(
    apis: dict[str, Any], coords: LatLon, filters: FilterState
) -> list[dict[str, Any]]:
    emergency: list[dict[str, Any]] = []
    if filters.show_police:
        emergency += _fetch_point_features(
            apis["Emergency"].get_police_stations, "Police Station", coords, filters.radius
        )
    if filters.show_fire:
        emergency += _fetch_point_features(
            apis["Emergency"].get_fire_stations, "Fire Station", coords, filters.radius
        )
    return emergency


def _fetch_infrastructure(
    apis: dict[str, Any], coords: LatLon, filters: FilterState
) -> list[dict[str, Any]]:
    infra: list[dict[str, Any]] = []
    if filters.show_bus_stops:
        infra += _fetch_point_features(
            apis["Bus Stops"].get_all_stops, "Bus Stop", coords, filters.radius
        )
    if filters.show_libraries:
        infra += _fetch_point_features(
            apis["Libraries"].get_all_libraries, "Library", coords, filters.radius
        )
    if filters.show_parks:
        try:
            infra += _fetch_point_features(
                apis["Parks"].get_all_parks, "Park", coords, filters.radius
            )
        except Exception as exc:
            logger.warning("Parks fetch failed: %s", exc)
    return infra


def _fetch_nearby_data(coords: LatLon, filters: FilterState) -> NearbyData:
    """Fetch all facility data near *coords* according to *filters*."""
    apis = _get_apis()
    zv = _get_zip_validator()
    closest_zip = zv.get_closest_zip(coords)
    nearby_zips = zv.get_nearby_zips(closest_zip, filters.radius) if closest_zip else []
    schools = _fetch_schools(nearby_zips, filters)
    healthcare: list[dict[str, Any]] = []
    if filters.show_hospitals:
        healthcare += _fetch_point_features(
            apis["Healthcare"].get_hospitals, "Hospital", coords, filters.radius
        )
    if filters.show_mental_health:
        healthcare += _fetch_point_features(
            apis["Healthcare"].get_mental_health_centers, "Mental Health Center", coords, filters.radius
        )
    if filters.show_clinics:
        healthcare += _fetch_point_features(
            apis["Healthcare"].get_free_standing_clinics, "Clinic", coords, filters.radius
        )
    emergency = _fetch_emergency(apis, coords, filters)
    infrastructure = _fetch_infrastructure(apis, coords, filters)
    flood_zones = _fetch_flood_zones(coords, filters.radius) if filters.show_flood_zones else []
    return {
        "schools": schools,
        "healthcare": healthcare,
        "emergency": emergency,
        "infrastructure": infrastructure,
        "geo_data": {"flood_zones": flood_zones},
    }


# ---------------------------------------------------------------------------
# Rendering helpers (no API calls allowed here)
# ---------------------------------------------------------------------------


def _safe_dataframe(rows: list[Any], cols: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    present = [c for c in cols if c in df.columns]
    return df[present] if present else df


def _render_proximity_tab(data: NearbyData, radius: float) -> None:
    st.subheader("📍 Proximity Analysis")
    counts = {
        "Schools": len(data["schools"]),
        "Healthcare": len(data["healthcare"]),
        "Emergency": len(data["emergency"]),
        "Infrastructure": len(data["infrastructure"]),
    }
    fig = px.bar(
        x=list(counts.keys()),
        y=list(counts.values()),
        title=f"Facilities Within {radius} Miles",
        labels={"x": "Facility Type", "y": "Count"},
        color=list(counts.keys()),
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("View Detailed Facility List"):
        if data["schools"]:
            st.subheader("Schools")
            st.dataframe(_safe_dataframe(data["schools"], ["NAME", "school_type", "ADDRESS", "ZIPCODE"]))
        for label, key in [
            ("Healthcare Facilities", "healthcare"),
            ("Emergency Services", "emergency"),
            ("Infrastructure", "infrastructure"),
        ]:
            if data[key]:
                st.subheader(label)
                st.dataframe(_safe_dataframe([f["properties"] for f in data[key]], ["NAME", "type", "ADDRESS"]))


def _render_coverage_tab(data: NearbyData) -> None:
    st.subheader("📊 Service Coverage Analysis")
    coverage = pd.DataFrame({
        "Category": ["Education", "Healthcare", "Emergency", "Infrastructure"],
        "Coverage Score": [
            min(len(data["schools"]) / COVERAGE_DIVISOR_SCHOOLS, COVERAGE_SCORE_MAX),
            min(len(data["healthcare"]) / COVERAGE_DIVISOR_HEALTHCARE, COVERAGE_SCORE_MAX),
            min(len(data["emergency"]) / COVERAGE_DIVISOR_EMERGENCY, COVERAGE_SCORE_MAX),
            min(len(data["infrastructure"]) / COVERAGE_DIVISOR_INFRASTRUCTURE, COVERAGE_SCORE_MAX),
        ],
    })
    fig = px.bar(
        coverage, x="Category", y="Coverage Score",
        title="Service Coverage (0-10 scale)", color="Category",
        color_discrete_sequence=CHART_COLOR_SEQUENCE,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.info("Coverage scores are normalized on a scale of 0–10, where 10 represents excellent coverage.")


def _render_risk_tab(data: NearbyData) -> None:
    st.subheader("⚠️ Risk Assessment")
    risk = pd.DataFrame({
        "Risk Factor": ["Flood Zone Coverage", "Emergency Service Access", "Healthcare Access", "Infrastructure Access"],
        "Risk Score": [
            min(len(data["geo_data"]["flood_zones"]) * RISK_WEIGHT_FLOOD, COVERAGE_SCORE_MAX),
            max(0, COVERAGE_SCORE_MAX - len(data["emergency"]) * RISK_WEIGHT_EMERGENCY),
            max(0, COVERAGE_SCORE_MAX - len(data["healthcare"]) * RISK_WEIGHT_HEALTHCARE),
            max(0, COVERAGE_SCORE_MAX - len(data["infrastructure"]) * RISK_WEIGHT_INFRASTRUCTURE),
        ],
    })
    fig = px.bar(
        risk, x="Risk Factor", y="Risk Score",
        title="Risk Assessment (Higher = Higher Risk)", color="Risk Factor",
        color_discrete_sequence=list(px.colors.sequential.Reds),
    )
    st.plotly_chart(fig, use_container_width=True)
    risk_score: float = float(risk["Risk Score"].mean())
    risk_color = "green" if risk_score < RISK_THRESHOLD_LOW else "orange" if risk_score < RISK_THRESHOLD_MEDIUM else "red"
    st.markdown(
        f"### Overall Risk Level: <span style='color:{risk_color}'>{risk_score:.1f}/10</span>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Flood Zones", len(data["geo_data"]["flood_zones"]), help="Flood zones in your area")
    c2.metric("Emergency Services", len(data["emergency"]), help="Emergency services in your area")
    c3.metric("Healthcare Facilities", len(data["healthcare"]), help="Healthcare facilities in your area")


def _render_tabs(data: NearbyData, radius: float) -> None:
    tab1, tab2, tab3 = st.tabs(["Proximity Analysis", "Service Coverage Analysis", "Risk Assessment"])
    with tab1:
        _render_proximity_tab(data, radius)
    with tab2:
        _render_coverage_tab(data)
    with tab3:
        _render_risk_tab(data)


def _render_overview_charts() -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(plot_schools_histogram(), use_container_width=True)
    with col2:
        st.plotly_chart(plot_fire_station_proximity_pie(), use_container_width=True)
    with col3:
        st.plotly_chart(plot_zip_park_density_treemap(), use_container_width=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    st.header("📊 Miami-Dade County Overview")
    _render_overview_charts()

    if not st.session_state.get("location_submitted"):
        st.info("Enter a location on the **Map Explorer** tab first.")
        return

    coords: LatLon = st.session_state["resolved_coords"]
    location_label: str = st.session_state.get("last_location", "")

    control_col, main_col = st.columns([1, 3])

    with control_col:
        st.subheader("Control Panel")
        st.caption(f"Showing data for: **{location_label}**")
        filters: FilterState = render_filter_sidebar()

    with main_col:
        st.header("🎯 Local Area Insights")
        st.success(f"Showing results for: {location_label}")
        try:
            data = _get_or_fetch(location_label, coords, filters)
            _render_tabs(data, filters.radius)
        except Exception as exc:
            logger.error("Dashboard analysis failed: %s", exc)
            st.error(f"Error processing location: {exc}")
