from typing import List, TYPE_CHECKING
from sqlmodel import Relationship

from src.db.models.base import BaseModel
from src.schemas.organization import OrganizationBase

if TYPE_CHECKING:
    from src.db.models.office import Office


class Organization(OrganizationBase, BaseModel, table=True):
    """
    Organization model representing a company that operates currency exchange offices.
    """

    # Relationships
    offices: List["Office"] = Relationship(back_populates="organization")
