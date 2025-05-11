import uuid
from sqlmodel import SQLModel, Field
from datetime import datetime, UTC


class RateBase(SQLModel):
    """
    Base schema for Rate model.
    """

    office_id: uuid.UUID = Field(foreign_key="office.id")
    currency: str = Field(index=True)  # Currency code (e.g., USD, EUR)
    buy_rate: float  # Rate at which the office buys the currency
    sell_rate: float  # Rate at which the office sells the currency
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
