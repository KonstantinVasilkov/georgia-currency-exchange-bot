from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from src.db.models.office import Office

class Rate(SQLModel, table=True):
    """
    Rate model representing currency exchange rates for a specific office.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    office_id: int = Field(foreign_key="office.id")
    currency: str = Field(index=True)  # Currency code (e.g., USD, EUR)
    buy_rate: float  # Rate at which the office buys the currency
    sell_rate: float  # Rate at which the office sells the currency
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    office: "Office" = Relationship(back_populates="rates")
