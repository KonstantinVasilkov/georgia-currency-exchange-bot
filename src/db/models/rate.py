from typing import TYPE_CHECKING
from sqlmodel import Relationship

from src.db.models.base import BaseModel
from src.db.schemas.rate import RateBase

if TYPE_CHECKING:
    from src.db.models.office import Office


class Rate(RateBase, BaseModel, table=True):
    """
    Rate model representing currency exchange rates for a specific office.
    """

    # Relationships
    office: "Office" = Relationship(back_populates="rates")
