"""
Schedule models for the application.
"""

from typing import TYPE_CHECKING
from sqlmodel import Relationship

from src.db.models.base import BaseModel
from src.schemas.schedule import ScheduleBase

if TYPE_CHECKING:
    from src.db.models.office import Office


class Schedule(ScheduleBase, BaseModel, table=True):
    """
    Schedule model representing working hours for a specific office.
    """

    # Relationships
    office: "Office" = Relationship(back_populates="schedules")
