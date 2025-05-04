import uuid
from sqlmodel import Field
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from datetime import datetime


class ExternalSchemaCustomModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class TopLevelRate(ExternalSchemaCustomModel):
    ccy: str
    buy: float
    sell: float
    nbg: float


class OrgRate(ExternalSchemaCustomModel):
    ccy: str
    buy: float
    sell: float


class OfficeRate(ExternalSchemaCustomModel):
    ccy: str
    buy: float
    sell: float
    time_from: datetime = Field(..., alias="timeFrom")
    time: datetime


class LocalizedName(ExternalSchemaCustomModel):
    en: str | None = None
    ka: str | None = None
    ru: str | None = None


class ScheduleEntry(ExternalSchemaCustomModel):
    start: LocalizedName
    end: LocalizedName | None = None
    intervals: list[str]


class Office(ExternalSchemaCustomModel):
    id: uuid.UUID
    name: LocalizedName
    address: LocalizedName
    icon: str | None = None
    working_now: bool | None = False
    rates: dict[str, OfficeRate]


class OfficeExtended(ExternalSchemaCustomModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    city_id: uuid.UUID
    city: LocalizedName
    longitude: float
    latitude: float
    name: LocalizedName
    address: LocalizedName
    office_icon: str
    icon: str
    working_now: bool
    working_24_7: bool
    schedule: list[ScheduleEntry]
    rates: dict[str, OfficeRate]


class Organization(ExternalSchemaCustomModel):
    id: uuid.UUID
    type: str
    link: str
    icon: str | None = None
    name: LocalizedName
    best: dict[str, OrgRate]
    offices: list[Office]


class ExchangeResponse(ExternalSchemaCustomModel):
    best: dict[str, TopLevelRate]
    organizations: list[Organization]


class MapResponse(ExternalSchemaCustomModel):
    best: dict[str, TopLevelRate]
    offices: list[OfficeExtended]
