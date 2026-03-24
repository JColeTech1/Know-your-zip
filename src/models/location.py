"""
Shared location / geometry models.

These are the trust boundary for all coordinate data that enters the app.
Nothing downstream should touch raw ArcGIS geometry dicts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    """WGS-84 latitude / longitude pair."""

    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

    @classmethod
    def from_arcgis(cls, coords: list[float]) -> "Coordinates":
        """ArcGIS returns [longitude, latitude] — note the reversal."""
        if len(coords) < 2:
            raise ValueError(f"Expected [lon, lat], got {coords}")
        return cls(lon=coords[0], lat=coords[1])


class ZipLocation(BaseModel):
    """A validated Miami-Dade ZIP code with its centroid coordinates."""

    zip_code: str = Field(..., pattern=r"^\d{5}$")
    lat: float
    lon: float
    name: str = ""

    @field_validator("zip_code")
    @classmethod
    def must_be_five_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError(f"ZIP code must be exactly 5 digits, got '{v}'")
        return v


class ArcGISFeature(BaseModel):
    """
    Minimal validated wrapper for a single ArcGIS GeoJSON feature.

    Use domain-specific models (School, Hospital, etc.) for richer validation.
    """

    type: str = "Feature"
    properties: dict[str, object]
    geometry: dict[str, object] | None = None

    @property
    def coordinates(self) -> Coordinates | None:
        """Return parsed coordinates from the geometry, or None if absent."""
        if not self.geometry:
            return None
        raw = self.geometry.get("coordinates")
        if not isinstance(raw, list) or len(raw) < 2:
            return None
        try:
            return Coordinates.from_arcgis(list(raw[:2]))
        except (ValueError, TypeError):
            return None

    def prop(self, *keys: str, default: str = "") -> str:
        """
        Return the first non-empty value among the given property key candidates.

        ArcGIS services use inconsistent casing (NAME vs name vs FACILITY_NAME).
        This helper centralises the fallback chain.
        """
        for key in keys:
            val = self.properties.get(key)
            if val is not None and str(val).strip():
                return str(val).strip()
        return default


class ArcGISFeatureCollection(BaseModel):
    """Validated GeoJSON FeatureCollection from an ArcGIS query."""

    type: str = "FeatureCollection"
    features: list[ArcGISFeature] = Field(default_factory=list)
