from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from src.db.models.organization import Organization
    from src.db.models.rate import Rate

class Office(SQLModel, table=True):
    """
    Office model representing a physical location where currency exchange services are provided.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    address: str
    lat: float  # Latitude coordinate
    lng: float  # Longitude coordinate
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")

    # Relationships
    organization: Optional["Organization"] = Relationship(back_populates="offices")
    rates: List["Rate"] = Relationship(back_populates="office")
