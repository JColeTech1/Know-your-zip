"""
Address geocoding helpers.

All address → coordinates lookups go through this module.
No other file should import geopy.geocoders directly.
"""

from __future__ import annotations

import logging

from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

from src.constants import AI_GEOCODER_USER_AGENT, API_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

# Type alias
LatLon = tuple[float, float]


def geocode_address(address: str) -> LatLon | None:
    """
    Convert a free-text address string to (lat, lon) using Nominatim.

    Returns None on any failure rather than raising, so callers can
    show a friendly error message to the user.
    """
    geolocator = Nominatim(user_agent=AI_GEOCODER_USER_AGENT)
    try:
        result = geolocator.geocode(address, timeout=API_TIMEOUT_SECONDS)
        if result is None:
            logger.info("Nominatim returned no result for address: %r", address)
            return None
        return (result.latitude, result.longitude)
    except GeocoderTimedOut:
        logger.warning("Geocoder timed out for address: %r", address)
        return None
    except GeocoderUnavailable as exc:
        logger.error("Geocoder unavailable: %s", exc)
        return None
