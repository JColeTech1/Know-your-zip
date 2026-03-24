"""
Know-Your-Zip — entry point.
Page config · CSS · session state · navigation · tab routing.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bootstrap import init_session_state, render_header
from src.styles import APP_CSS

# MUST be the first Streamlit command
st.set_page_config(
    page_title="Miami-Dade County Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

init_session_state()
render_header()

# Navigation
nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📊 Dashboard", help="County-wide analytics", use_container_width=True):
        st.session_state.current_page = "Dashboard"
with nav2:
    if st.button("🗺️ Map Explorer", help="Interactive map", use_container_width=True):
        st.session_state.current_page = "Map"
with nav3:
    if st.button("🤖 AI Assistant", help="Chat with AI", use_container_width=True):
        st.session_state.current_page = "Bot"

st.markdown("---")

# Tab routing — delegate all logic to tab modules
if st.session_state.current_page == "Dashboard":
    from src.ui import dashboard
    dashboard.main()
elif st.session_state.current_page == "Map":
    import map_explorer
    map_explorer.main()
elif st.session_state.current_page == "Bot":
    from src.ui import ai_assistant
    ai_assistant.main()

st.markdown("---")
st.markdown(
    "<div style='text-align:center'><p>Miami-Dade County Explorer | Built with Streamlit</p></div>",
    unsafe_allow_html=True,
)
