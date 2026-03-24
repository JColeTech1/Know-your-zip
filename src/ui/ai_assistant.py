"""
AI Assistant tab — chat interface powered by Llama 3.3 via Together.ai.

Responsibilities:
  1. Resolve user location → share resolved_coords / last_location with other tabs
  2. Build location context from nearby data via src/ui/data_fetcher.py
  3. Maintain chat history in session state
  4. Call Together.ai chat completions API
"""

from __future__ import annotations

import logging
import os
import re

import streamlit as st
from together import Together

from src.api.education import EducationAPI
from src.api.emergency import EmergencyServicesAPI
from src.api.geo import GeoDataAPI
from src.api.healthcare import HealthcareAPI
from src.api.infrastructure import BusStopsAPI, LibrariesAPI, ParksAPI
from src.constants import (
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_TEMPERATURE,
    ZIP_CODE_PATTERN,
)
from src.ui.data_fetcher import build_markers
from src.ui.filters import FilterState, render_filter_sidebar
from src.utils.geocoder import geocode_address
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)
_ZIP_RE = re.compile(ZIP_CODE_PATTERN)

LatLon = tuple[float, float]


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


@st.cache_resource
def get_together_client() -> Together:
    api_key = os.getenv("TOGETHER_API_KEY") or st.secrets.get("TOGETHER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "TOGETHER_API_KEY not set in .env or Streamlit secrets."
        )
    return Together(api_key=api_key)


# ---------------------------------------------------------------------------
# Location resolution
# ---------------------------------------------------------------------------

def _resolve_location(
    location_input: str,
    zip_validator: ZIPValidator,
) -> LatLon | None:
    """Return (lat, lon) for a ZIP or free-text address, or None on failure."""
    if _ZIP_RE.match(location_input.strip()):
        is_valid, message, _ = zip_validator.validate_zip(location_input)
        if not is_valid:
            st.error(message)
            return None
        coords = zip_validator.get_zip_coordinates(location_input)
        if not coords:
            st.error("Could not get coordinates for this ZIP code.")
        return coords
    coords = geocode_address(location_input)
    if not coords:
        st.error("Could not find coordinates for the provided location.")
    return coords


# ---------------------------------------------------------------------------
# AI context and response
# ---------------------------------------------------------------------------

def _build_context_summary(
    location: str,
    radius: float,
    markers: list[dict],
) -> str:
    """Return a text summary of nearby facilities for the AI system prompt."""
    counts: dict[str, int] = {}
    for m in markers:
        if m.get("is_user_location"):
            continue
        icon: str = m.get("icon", "other")
        counts[icon] = counts.get(icon, 0) + 1

    parts = [f"User location: {location}. Searching within {radius:.1f} miles."]
    category_labels: list[tuple[str, str]] = [
        ("public_school", "public schools"),
        ("private_school", "private schools"),
        ("charter_school", "charter schools"),
        ("police", "police stations"),
        ("fire", "fire stations"),
        ("hospital", "hospitals"),
        ("mental_health", "mental health centers"),
        ("clinic", "clinics"),
        ("bus_stop", "bus stops"),
        ("library", "libraries"),
        ("park", "parks"),
    ]
    found = [f"{counts[k]} {label}" for k, label in category_labels if counts.get(k)]
    if found:
        parts.append("Nearby: " + ", ".join(found) + ".")
    else:
        parts.append("No facilities found in the selected categories.")
    return " ".join(parts)


def _build_system_prompt(context: str) -> str:
    return (
        "You are a knowledgeable assistant specializing in Miami-Dade County, Florida. "
        "Answer questions about neighborhoods, services, schools, healthcare, emergency "
        "services, infrastructure, and geographic features. Be concise and factual. "
        f"Current data context: {context}"
    )


def _get_ai_response(
    client: Together,
    messages: list[dict[str, str]],
    system_prompt: str,
) -> str:
    """Call Together chat completions and return the assistant reply."""
    api_messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=api_messages,
        max_tokens=AI_MAX_TOKENS,
        temperature=AI_TEMPERATURE,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Location submit handler
# ---------------------------------------------------------------------------

def _handle_location_submit(
    location_input: str,
    filters: FilterState,
    apis: dict,
    zip_validator: ZIPValidator,
) -> None:
    """Resolve location, build context, update session state, rerun."""
    cached = (
        st.session_state.get("resolved_coords") is not None
        and st.session_state.get("last_location") == location_input
    )
    if cached:
        coords: LatLon = st.session_state.resolved_coords
    else:
        with st.spinner("Resolving location…"):
            result = _resolve_location(location_input, zip_validator)
        if not result:
            return
        coords = result
        st.session_state.resolved_coords = coords
        st.session_state.last_location = location_input

    with st.spinner("Fetching nearby data…"):
        markers = build_markers(apis, zip_validator, coords, filters)

    context = _build_context_summary(location_input, filters.radius, markers)
    st.session_state.location_data = context
    st.rerun()


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------

def _render_location_panel(
    apis: dict,
    zip_validator: ZIPValidator,
) -> None:
    """Render left column: location input + filter sidebar."""
    st.subheader("📍 Location Information")

    coords = st.session_state.get("resolved_coords")
    last: str = st.session_state.get("last_location", "")
    if coords and last:
        st.success(f"Currently showing: **{last}**")

    with st.form(key="ai_location_form", clear_on_submit=False):
        in_col, btn_col = st.columns([4, 1])
        with in_col:
            location_input = st.text_input(
                "Enter your address or ZIP code",
                key="location_input",
            )
        with btn_col:
            submitted = st.form_submit_button("Enter Location")
        filters = render_filter_sidebar()

    if submitted:
        if not location_input:
            st.error("Please enter an address or ZIP code.")
        else:
            _handle_location_submit(location_input, filters, apis, zip_validator)


def _render_chat_panel(client: Together) -> None:
    """Render right column: chat history + message input."""
    st.subheader("💬 Chat with AI Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your message here...", height=80)
        send = st.form_submit_button("Send")

    if send and user_input.strip():
        _handle_chat_send(client, user_input.strip())


def _handle_chat_send(client: Together, user_input: str) -> None:
    """Append user message, get AI reply, update session state."""
    st.session_state.messages.append({"role": "user", "content": user_input})
    raw_context = st.session_state.get("location_data")
    context: str = (
        raw_context
        if isinstance(raw_context, str)
        else "No location selected. Answer general Miami-Dade County questions."
    )
    system_prompt = _build_system_prompt(context)
    try:
        reply = _get_ai_response(client, st.session_state.messages, system_prompt)
    except Exception as exc:
        logger.exception("Together API error: %s", exc)
        st.error(f"AI error: {exc}")
        st.session_state.messages.pop()  # remove the unsent user message
        return
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point called by app.py."""
    st.title("🤖 Miami-Dade County AI Assistant")
    st.write(
        "Ask questions about neighborhoods, schools, healthcare, emergency services, "
        "and more in Miami-Dade County."
    )

    try:
        client = get_together_client()
    except RuntimeError as exc:
        st.error(str(exc))
        st.stop()

    apis = get_apis()
    zip_validator = get_zip_validator()

    col1, col2 = st.columns([1, 2])
    with col1:
        _render_location_panel(apis, zip_validator)
    with col2:
        _render_chat_panel(client)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
