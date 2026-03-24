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
)
from src.ui.data_fetcher import build_markers
from src.ui.filters import FilterState, render_filter_sidebar, render_location_form
from src.zip_validator import ZIPValidator

logger = logging.getLogger(__name__)

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
# Context auto-build
# ---------------------------------------------------------------------------

def _ensure_location_context(
    apis: dict,
    zip_validator: ZIPValidator,
    filters: FilterState,
) -> None:
    """Build location_data from session state if not already built for current location."""
    raw = st.session_state.get("resolved_coords")
    location: str = st.session_state.get("last_location", "")
    if not location or not isinstance(raw, (tuple, list)) or len(raw) != 2:
        if raw is not None and not (isinstance(raw, (tuple, list)) and len(raw) == 2):
            st.session_state.resolved_coords = None
            st.session_state.location_submitted = False
        return
    coords: LatLon = raw  # type: ignore[assignment]
    context_key = f"{location}|{filters.radius}"
    if st.session_state.get("ai_context_key") == context_key:
        return
    with st.spinner("Building location context…"):
        markers = build_markers(apis, zip_validator, coords, filters)
    context = _build_context_summary(location, filters.radius, markers)
    st.session_state.location_data = context
    st.session_state.ai_context_key = context_key


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------

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

    # Location entry — available on all tabs
    render_location_form()
    location_label: str = st.session_state.get("last_location", "")
    if location_label:
        st.caption(f"📍 Location context: **{location_label}**")

    # Filter sidebar drives context granularity
    filters: FilterState = render_filter_sidebar()

    # Auto-build location context whenever location or radius changes
    if st.session_state.get("location_submitted"):
        apis = get_apis()
        zip_validator = get_zip_validator()
        _ensure_location_context(apis, zip_validator, filters)

    _render_chat_panel(client)

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
