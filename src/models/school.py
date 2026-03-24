"""Pydantic models for school data (public, private, charter)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.models.location import ArcGISFeature, Coordinates


class SchoolType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    CHARTER = "charter"


class School(BaseModel):
    """Normalised school record derived from an ArcGISFeature."""

    name: str
    address: str
    phone: str
    school_type: SchoolType
    zip_code: str
    coordinates: Coordinates
    distance_miles: float = Field(default=0.0, ge=0.0)

    @classmethod
    def from_feature(
        cls,
        feature: ArcGISFeature,
        school_type: SchoolType,
        distance_miles: float = 0.0,
    ) -> "School":
        coords = feature.coordinates
        if coords is None:
            raise ValueError("Feature has no parseable geometry")

        props = feature.properties
        zip_raw = str(props.get("ZIPCODE", props.get("ZIP_CODE", props.get("ZIP", ""))))
        zip_code = zip_raw[:5] if len(zip_raw) >= 5 else zip_raw

        return cls(
            name=feature.prop("NAME", "name", "SCHOOL_NAME", default="Unknown"),
            address=feature.prop("ADDRESS", "address", "STREET_ADDRESS", default=""),
            phone=feature.prop("PHONE", "phone", "PHONE_NUMBER", default=""),
            school_type=school_type,
            zip_code=zip_code,
            coordinates=coords,
            distance_miles=distance_miles,
        )
