"""Pydantic models for infrastructure data (bus stops, libraries, parks)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.models.location import ArcGISFeature, Coordinates


class InfrastructureType(str, Enum):
    BUS_STOP = "bus_stop"
    LIBRARY = "library"
    PARK = "park"


class InfrastructureFacility(BaseModel):
    """Normalised infrastructure facility record."""

    name: str
    address: str
    facility_type: InfrastructureType
    coordinates: Coordinates
    phone: str = ""
    route: str = ""      # for bus stops
    hours: str = ""      # for libraries / parks
    amenities: str = ""  # for parks
    distance_miles: float = Field(default=0.0, ge=0.0)

    @classmethod
    def from_feature(
        cls,
        feature: ArcGISFeature,
        facility_type: InfrastructureType,
        distance_miles: float = 0.0,
    ) -> "InfrastructureFacility":
        coords = feature.coordinates
        if coords is None:
            raise ValueError("Feature has no parseable geometry")

        return cls(
            name=feature.prop("NAME", "name", "FACILITY_NAME", default="Unknown"),
            address=feature.prop("ADDRESS", "address", "STREET_ADDRESS", default=""),
            facility_type=facility_type,
            coordinates=coords,
            phone=feature.prop("PHONE", "phone", "PHONE_NUMBER", default=""),
            route=feature.prop("ROUTE", "route", "BUS_ROUTE", default=""),
            hours=feature.prop("HOURS", "hours", "OPERATING_HOURS", default=""),
            amenities=feature.prop("AMENITIES", "amenities", "FACILITIES", default=""),
            distance_miles=distance_miles,
        )
