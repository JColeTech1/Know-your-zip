"""
County-wide overview charts for the Dashboard tab.

UI only: generates Plotly figures from ArcGIS data.
No Streamlit widgets here — callers render the figures with st.plotly_chart().
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.api.education import EducationAPI
from src.api.emergency import EmergencyServicesAPI
from src.api.infrastructure import ParksAPI
from src.constants import (
    CACHE_KEY_SCHOOLS_BY_LEVEL,
    CHART_BAR_TEXT_FONT_SIZE,
    CHART_HEIGHT,
    CHART_SCHOOL_BARMODE,
    CHART_TITLE_FONT_SIZE,
    COLOR_ACCENT_2,
    COLOR_CORAL_LIGHTEST,
    COLOR_CORAL_MEDIUM,
    COLOR_SCHOOL_CHARTER,
    COLOR_SCHOOL_PRIVATE,
    COLOR_SCHOOL_PUBLIC,
    COLOR_SECONDARY,
    FIRE_PROXIMITY_CLOSE_MAX,
    FIRE_PROXIMITY_LABEL_CLOSE,
    FIRE_PROXIMITY_LABEL_FAR,
    FIRE_PROXIMITY_LABEL_MEDIUM,
    FIRE_PROXIMITY_LABEL_NEAR,
    FIRE_PROXIMITY_MEDIUM_MAX,
    FIRE_PROXIMITY_NEAR_MAX,
    MAX_FEATURES_PER_REQUEST,
    SCHOOL_LEVEL_ELEMENTARY,
    SCHOOL_LEVEL_HIGH,
    SCHOOL_LEVEL_MIDDLE,
)
from src.utils.data_loader import load_pickle, save_pickle
from src.utils.distance import miles_between
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)

# LatLon type alias reused from src.utils.distance convention
LatLon = tuple[float, float]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _empty_fig(message: str) -> go.Figure:
    """Return a blank figure with a centred annotation (used on data errors)."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 14},
    )
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return fig


def _title_layout(text: str) -> dict[str, Any]:
    """Return a standard Plotly title dict."""
    return {
        "text": text,
        "y": 0.95,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
        "font": {"size": CHART_TITLE_FONT_SIZE},
    }


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _categorize_school_level(name: str) -> str:
    """Infer school level (Elementary / Middle / High) from the school name."""
    upper = name.upper()
    if "HIGH" in upper:
        return SCHOOL_LEVEL_HIGH
    if "MIDDLE" in upper or "JUNIOR" in upper:
        return SCHOOL_LEVEL_MIDDLE
    return SCHOOL_LEVEL_ELEMENTARY


def _get_all_schools_county_wide() -> dict[str, dict[str, int]]:
    """
    Fetch all Miami-Dade schools and tally counts by (level, type).

    Checks the pickle disk cache first (key: CACHE_KEY_SCHOOLS_BY_LEVEL);
    falls back to 3 ArcGIS calls on a cache miss.

    Returns:
        {level: {"public": N, "private": N, "charter": N}}
        where level ∈ {SCHOOL_LEVEL_ELEMENTARY, SCHOOL_LEVEL_MIDDLE, SCHOOL_LEVEL_HIGH}
    """
    cached = load_pickle(CACHE_KEY_SCHOOLS_BY_LEVEL, dict)
    if cached is not None:
        logger.debug("_get_all_schools_county_wide: cache hit")
        return cached  # type: ignore[return-value]

    counts: dict[str, dict[str, int]] = {
        SCHOOL_LEVEL_ELEMENTARY: {"public": 0, "private": 0, "charter": 0},
        SCHOOL_LEVEL_MIDDLE: {"public": 0, "private": 0, "charter": 0},
        SCHOOL_LEVEL_HIGH: {"public": 0, "private": 0, "charter": 0},
    }

    education_api = EducationAPI()
    school_types = ["public", "private", "charter"]

    for school_type in school_types:
        result = education_api.get_all_schools(school_type)
        if not result.get("success"):
            logger.warning("Could not fetch %s schools: %s", school_type, result.get("error"))
            continue
        features: list[Any] = result["data"]["schools"][:MAX_FEATURES_PER_REQUEST]
        for feature in features:
            props: dict[str, Any] = feature.get("properties") or {}
            name = str(props.get("NAME") or props.get("SCHOOL_NAME") or "")
            level = _categorize_school_level(name)
            counts[level][school_type] += 1

    save_pickle(CACHE_KEY_SCHOOLS_BY_LEVEL, counts)
    return counts


# ---------------------------------------------------------------------------
# Public chart functions
# ---------------------------------------------------------------------------


def plot_schools_histogram() -> go.Figure:
    """
    Stacked bar chart: school counts by level (Elementary / Middle / High School)
    broken down by school type (Public / Private / Charter).
    """
    counts = _get_all_schools_county_wide()
    levels = [SCHOOL_LEVEL_ELEMENTARY, SCHOOL_LEVEL_MIDDLE, SCHOOL_LEVEL_HIGH]

    def _bar_text(lvl: str, stype: str) -> str:
        n = counts[lvl][stype]
        return str(n) if n > 0 else ""

    traces = [
        go.Bar(
            name="Public",
            x=levels,
            y=[counts[lvl]["public"] for lvl in levels],
            marker_color=COLOR_SCHOOL_PUBLIC,
            text=[_bar_text(lvl, "public") for lvl in levels],
            textposition="inside",
            textfont={"size": CHART_BAR_TEXT_FONT_SIZE, "color": "white"},
            insidetextanchor="middle",
        ),
        go.Bar(
            name="Private",
            x=levels,
            y=[counts[lvl]["private"] for lvl in levels],
            marker_color=COLOR_SCHOOL_PRIVATE,
            text=[_bar_text(lvl, "private") for lvl in levels],
            textposition="inside",
            textfont={"size": CHART_BAR_TEXT_FONT_SIZE, "color": "white"},
            insidetextanchor="middle",
        ),
        go.Bar(
            name="Charter",
            x=levels,
            y=[counts[lvl]["charter"] for lvl in levels],
            marker_color=COLOR_SCHOOL_CHARTER,
            text=[_bar_text(lvl, "charter") for lvl in levels],
            textposition="inside",
            textfont={"size": CHART_BAR_TEXT_FONT_SIZE, "color": "white"},
            insidetextanchor="middle",
        ),
    ]

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode=CHART_SCHOOL_BARMODE,
        title=_title_layout("School Distribution by Level"),
        xaxis_title="School Level",
        yaxis_title="Number of Schools",
        legend_title_text="School Type",
        bargap=0.2,
    )
    return fig


@st.cache_data
def plot_fire_station_proximity_pie() -> go.Figure:
    """
    Donut chart: ZIP codes grouped by distance to nearest fire station.

    Distance categories (miles): 0-1, 2-3, 4-5, 6+
    """
    emergency_api = EmergencyServicesAPI()
    zip_validator = ZIPValidator()

    fire_stations = emergency_api.get_fire_stations()
    if fire_stations is None:
        logger.error("plot_fire_station_proximity_pie: fire stations API returned None")
        return _empty_fig("Fire station data unavailable.")

    zip_codes = list(zip_validator.get_all_zip_codes())[:MAX_FEATURES_PER_REQUEST]
    features: list[Any] = fire_stations.get("features", [])[:MAX_FEATURES_PER_REQUEST]

    distance_categories: dict[str, int] = {
        FIRE_PROXIMITY_LABEL_NEAR: 0,
        FIRE_PROXIMITY_LABEL_CLOSE: 0,
        FIRE_PROXIMITY_LABEL_MEDIUM: 0,
        FIRE_PROXIMITY_LABEL_FAR: 0,
    }

    for zip_code in zip_codes:
        zip_coords: LatLon | None = zip_validator.get_zip_coordinates(zip_code)
        if zip_coords is None:
            continue

        min_dist = float("inf")
        for station in features:
            geom = station.get("geometry")
            if not geom:
                continue
            coords = geom.get("coordinates")
            if not coords:
                continue
            station_coords: LatLon = (coords[1], coords[0])
            dist = miles_between(zip_coords, station_coords)
            if dist < min_dist:
                min_dist = dist

        if min_dist <= FIRE_PROXIMITY_NEAR_MAX:
            distance_categories[FIRE_PROXIMITY_LABEL_NEAR] += 1
        elif min_dist <= FIRE_PROXIMITY_CLOSE_MAX:
            distance_categories[FIRE_PROXIMITY_LABEL_CLOSE] += 1
        elif min_dist <= FIRE_PROXIMITY_MEDIUM_MAX:
            distance_categories[FIRE_PROXIMITY_LABEL_MEDIUM] += 1
        else:
            distance_categories[FIRE_PROXIMITY_LABEL_FAR] += 1

    df = pd.DataFrame(
        {
            "Distance": list(distance_categories.keys()),
            "ZIP Codes": list(distance_categories.values()),
        }
    ).sort_values("ZIP Codes", ascending=False)

    colors = [COLOR_CORAL_LIGHTEST, COLOR_ACCENT_2, COLOR_CORAL_MEDIUM, COLOR_SECONDARY]
    total = sum(distance_categories.values())

    fig = px.pie(
        df,
        values="ZIP Codes",
        names="Distance",
        title="Fire Station Coverage",
        color_discrete_sequence=colors,
        hole=0.3,
    )
    fig.update_layout(
        title=_title_layout("Fire Station Coverage"),
        legend_title_text="Distance to Nearest Fire Station",
        annotations=[
            {
                "text": f"<b>Total ZIP:<br>{total}</b>",
                "x": 0.5,
                "y": 0.5,
                "font": {"size": 14, "color": "black", "family": "Arial Black"},
                "showarrow": False,
                "align": "center",
            }
        ],
    )
    return fig


@st.cache_data
def plot_zip_park_density_treemap() -> go.Figure:
    """
    Treemap: ZIP code area sized by sq-miles, coloured by park count.
    """
    zip_validator = ZIPValidator()
    parks_api = ParksAPI()

    parks_data: dict[str, Any] = parks_api.get_all_parks() or {"features": []}
    zip_codes = list(zip_validator.get_all_zip_codes())[:MAX_FEATURES_PER_REQUEST]
    features: list[Any] = parks_data.get("features", [])[:MAX_FEATURES_PER_REQUEST]

    rows: list[dict[str, Any]] = []
    for zip_code in zip_codes:
        zip_area = zip_validator.get_zip_area(zip_code)
        park_count = 0
        for park in features:
            geom = park.get("geometry")
            if not geom:
                continue
            coords = geom.get("coordinates")
            if not coords:
                continue
            if zip_validator.is_point_in_zip(coords[1], coords[0], zip_code):
                park_count += 1
        rows.append(
            {
                "ZIP_Code": zip_code,
                "Area": zip_area,
                "Park_Count": park_count,
            }
        )

    if not rows:
        return _empty_fig("No park data available.")

    df = pd.DataFrame(rows)
    fig = px.treemap(
        df,
        path=[px.Constant("Miami-Dade"), "ZIP_Code"],
        values="Area",
        color="Park_Count",
        color_continuous_scale="Greens",
        title="Park Locations and Density",
        custom_data=["Park_Count"],
    )
    fig.update_traces(
        hovertemplate=(
            "ZIP Code: %{label}<br>"
            "Parks: %{customdata[0]}<br>"
            "Area: %{value:.1f} sq mi<br>"
            "<extra></extra>"
        ),
        textinfo="label",
        texttemplate="<b>%{label}</b>",
    )
    fig.update_layout(
        title=_title_layout("Park Locations and Density"),
        height=CHART_HEIGHT,
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        showlegend=False,
    )
    return fig
