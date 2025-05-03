from typing import Optional
import uuid
from sqlmodel import SQLModel, Field


class OfficeBase(SQLModel):
    """
    Base schema for Office model.
    """

    name: str = Field(index=True)
    address: str
    lat: float  # Latitude coordinate
    lng: float  # Longitude coordinate
    organization_id: Optional[uuid.UUID] = Field(
        default=None, foreign_key="organization.id"
    )
    external_ref_id: Optional[str] = None
