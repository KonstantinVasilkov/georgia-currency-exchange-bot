"""
Office repository for database operations.

This module provides a repository for Office model operations.
"""

from typing import List, Sequence
import uuid
from sqlalchemy import true
from sqlmodel import select, col
from datetime import datetime, UTC

from src.db.models.office import Office
from src.repositories.base_repository import AsyncBaseRepository


class AsyncOfficeRepository(AsyncBaseRepository[Office]):
    """
    Async repository for Office model operations.
    """

    def __init__(self, session):
        super().__init__(model_class=Office, session=session)

    async def get_active_offices(
        self, skip: int = 0, limit: int = 100
    ) -> Sequence[Office]:
        statement = (
            select(Office).where(Office.is_active == true()).offset(skip).limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_organization(self, organization_id: uuid.UUID) -> Sequence[Office]:
        statement = select(Office).where(Office.organization_id == organization_id)
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_coordinates(
        self, lat: float, lng: float, radius: float = 1.0
    ) -> Sequence[Office]:
        degree_radius = radius / 111.0
        statement = (
            select(Office)
            .where(Office.is_active == true())
            .where(Office.lat >= lat - degree_radius)
            .where(Office.lat <= lat + degree_radius)
            .where(Office.lng >= lng - degree_radius)
            .where(Office.lng <= lng + degree_radius)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def mark_inactive_if_not_in_list(self, active_ids: List[uuid.UUID]) -> int:
        if not active_ids:
            return 0
        statement = (
            select(Office)
            .where(Office.is_active == true())
            .where(col(Office.id).not_in(active_ids))
        )
        offices_to_deactivate = (await self.session.exec(statement)).all()
        for office in offices_to_deactivate:
            office.is_active = False
            office.updated_at = datetime.now(tz=UTC)
            self.session.add(office)
        await self.session.commit()
        return len(offices_to_deactivate)

    async def upsert(self, office_data: dict) -> Office:
        existing_office = await self.find_one_by(
            name=office_data.get("name"),
            organization_id=office_data.get("organization_id"),
        )
        if existing_office:
            office_data["updated_at"] = datetime.now(tz=UTC)
            return await self.update(db_obj=existing_office, obj_in=office_data)
        else:
            return await self.create(obj_in=office_data)
