from typing import Optional
from sqlmodel import SQLModel, Field


class OrganizationBase(SQLModel):
    """
    Base schema for Organization model.
    """

    external_ref_id: Optional[str] = None
    name: str = Field(index=True)
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
