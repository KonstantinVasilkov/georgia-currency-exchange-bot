import uuid
from sqlmodel import Field
from datetime import datetime

from src.db.models import BaseModel


class TopLevelRate(BaseModel):
    ccy: str
    buy: float
    sell: float
    nbg: float


class OrgRate(BaseModel):
    ccy: str
    buy: float
    sell: float


class OfficeRate(BaseModel):
    ccy: str
    buy: float
    sell: float
    time_from: datetime = Field(..., alias="timeFrom")
    time: datetime

    class Config:
        allow_population_by_field_name = True


class LocalizedName(BaseModel):
    en: str
    ka: str
    ru: str | None = None


class ScheduleEntry(BaseModel):
    start: LocalizedName
    end: LocalizedName | None = None
    intervals: list[str]


class Office(BaseModel):
    id: uuid.UUID
    name: LocalizedName
    address: LocalizedName
    icon: str | None = None
    working_now: bool | None = False
    rates: dict[str, OfficeRate]

    class Config:
        allow_population_by_field_name = True


class OfficeExtended(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID = Field(..., alias="organizationId")
    city_id: uuid.UUID = Field(..., alias="cityId")
    city: LocalizedName
    longitude: float
    latitude: float
    name: LocalizedName
    address: LocalizedName
    office_icon: str = Field(..., alias="officeIcon")
    icon: str
    working_now: bool
    working_24_7: bool = Field(..., alias="working_24_7")
    schedule: list[ScheduleEntry]
    rates: dict[str, OfficeRate]

    class Config:
        allow_population_by_field_name = True


class Organization(BaseModel):
    id: uuid.UUID
    type: str
    link: str
    icon: str | None = None
    name: LocalizedName
    best: dict[str, OrgRate]
    offices: list[Office]


class ExchangeResponse(BaseModel):
    best: dict[str, TopLevelRate]
    organizations: list[Organization]


class MapResponse(BaseModel):
    best: dict[str, TopLevelRate]
    offices: list[OfficeExtended]
