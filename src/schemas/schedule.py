"""
Schedule schemas for the application.
"""

import uuid
from sqlmodel import SQLModel, Field


class ScheduleBase(SQLModel):
    """
    Base schema for Schedule model.
    """

    day: int = Field(description="Day of the week (0-6, where 0 is Monday)")
    opens_at: int = Field(description="Opening time in minutes from midnight")
    closes_at: int = Field(description="Closing time in minutes from midnight")
    office_id: uuid.UUID = Field(foreign_key="office.id")
