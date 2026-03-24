"""
App-level session state bootstrap and header rendering.

Called once at app startup from app.py.
"""

from __future__ import annotations

import streamlit as st

from src.constants import MIAMI_DEFAULT_LAT, MIAMI_DEFAULT_LON, MIAMI_DEFAULT_ZOOM

_DEFAULTS: dict = {
    "current_page": "Dashboard",
    "location_input": "",
    "map_center": [MIAMI_DEFAULT_LAT, MIAMI_DEFAULT_LON],
    "zoom_level": MIAMI_DEFAULT_ZOOM,
    "markers": [],
    "messages": [],
    "location_data": None,
    # Shared across tabs: set by map_explorer when a location is successfully resolved
    "resolved_coords": None,   # tuple[float, float] | None
    "fetch_key": None,         # str | None — hash of (location + radius + filter flags)
}


def init_session_state() -> None:
    """Populate session state keys that haven't been set yet."""
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    """Render the logo + title header row."""
    logo_col, title_col = st.columns([1, 2])
    with logo_col:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("assets/miami-logo-zip.png", use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with title_col:
        st.markdown(
            '<div class="title-text">'
            '<span class="title-text-line">Miami-Dade</span>'
            '<span class="title-text-line">County Explorer</span>'
            "</div>",
            unsafe_allow_html=True,
        )
