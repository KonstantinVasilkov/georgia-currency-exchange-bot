from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Relationship

from src.db.models.base import BaseModel
from src.schemas.office import OfficeBase

if TYPE_CHECKING:
    from src.db.models.organization import Organization
    from src.db.models.rate import Rate


class Office(OfficeBase, BaseModel, table=True):
    """
    Office model representing a physical location where currency exchange services are provided.
    """

    # Relationships
    organization: Optional["Organization"] = Relationship(back_populates="offices")
    rates: List["Rate"] = Relationship(back_populates="office")
