from datetime import datetime
import uuid
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """
    Base model with common fields for all models.
    """

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
