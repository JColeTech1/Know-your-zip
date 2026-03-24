"""Pydantic models for healthcare facility data."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.models.location import ArcGISFeature, Coordinates


class FacilityType(str, Enum):
    HOSPITAL = "hospital"
    MENTAL_HEALTH = "mental_health"
    CLINIC = "clinic"


class HealthcareFacility(BaseModel):
    """Normalised healthcare facility record."""

    name: str
    address: str
    phone: str
    facility_type: FacilityType
    coordinates: Coordinates
    beds: str = ""
    services: str = ""
    hours: str = ""
    distance_miles: float = Field(default=0.0, ge=0.0)

    @classmethod
    def from_feature(
        cls,
        feature: ArcGISFeature,
        facility_type: FacilityType,
        distance_miles: float = 0.0,
    ) -> "HealthcareFacility":
        coords = feature.coordinates
        if coords is None:
            raise ValueError("Feature has no parseable geometry")

        return cls(
            name=feature.prop("NAME", "name", "FACILITY_NAME", default="Unknown"),
            address=feature.prop("ADDRESS", "address", "STREET_ADDRESS", default=""),
            phone=feature.prop("PHONE", "phone", "PHONE_NUMBER", default=""),
            facility_type=facility_type,
            coordinates=coords,
            beds=feature.prop("BEDS", "NUM_BEDS", default=""),
            services=feature.prop("SERVICES", "SERVICE_TYPE", default=""),
            hours=feature.prop("HOURS", "OPERATING_HOURS", default=""),
            distance_miles=distance_miles,
        )
