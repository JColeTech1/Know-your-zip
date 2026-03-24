"""Pydantic models for emergency service data (police, fire)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.models.location import ArcGISFeature, Coordinates


class ServiceType(str, Enum):
    POLICE = "police"
    FIRE = "fire"


class EmergencyService(BaseModel):
    """Normalised emergency service record."""

    name: str
    address: str
    phone: str
    service_type: ServiceType
    coordinates: Coordinates
    distance_miles: float = Field(default=0.0, ge=0.0)

    @classmethod
    def from_feature(
        cls,
        feature: ArcGISFeature,
        service_type: ServiceType,
        distance_miles: float = 0.0,
    ) -> "EmergencyService":
        coords = feature.coordinates
        if coords is None:
            raise ValueError("Feature has no parseable geometry")

        return cls(
            name=feature.prop("NAME", "name", "STATION_NAME", default="Unknown"),
            address=feature.prop("ADDRESS", "address", "STREET_ADDRESS", default=""),
            phone=feature.prop("PHONE", "phone", "PHONE_NUMBER", default=""),
            service_type=service_type,
            coordinates=coords,
            distance_miles=distance_miles,
        )
