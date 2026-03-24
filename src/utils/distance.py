"""
Geodesic distance helpers.

All distance calculations in the app go through this module.
No other file should import geopy.distance directly.
"""

from __future__ import annotations

from geopy.distance import geodesic

# Type alias: (lat, lon)
LatLon = tuple[float, float]


def miles_between(point_a: LatLon, point_b: LatLon) -> float:
    """Return the geodesic distance in miles between two (lat, lon) pairs."""
    return geodesic(point_a, point_b).miles


def is_within_radius(
    center: LatLon,
    point: LatLon,
    radius_miles: float,
) -> bool:
    """Return True if *point* is within *radius_miles* of *center*."""
    return miles_between(center, point) <= radius_miles


def nearest_point(
    center: LatLon,
    candidates: list[LatLon],
) -> LatLon | None:
    """
    Return the candidate point closest to *center*, or None if the list is empty.
    """
    if not candidates:
        return None
    return min(candidates, key=lambda p: miles_between(center, p))
