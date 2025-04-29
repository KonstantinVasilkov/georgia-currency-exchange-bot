from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from src.db.models.office import Office


class Organization(SQLModel, table=True):
    """
    Organization model representing a company that operates currency exchange offices.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None

    # Relationships
    offices: List["Office"] = Relationship(back_populates="organization")
