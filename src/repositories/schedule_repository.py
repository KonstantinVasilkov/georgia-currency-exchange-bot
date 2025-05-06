"""
Repository for handling schedule operations.
"""

from typing import List, Sequence
from uuid import UUID

from sqlmodel import select

from src.db.models.schedule import Schedule
from src.repositories.base_repository import AsyncBaseRepository


class AsyncScheduleRepository(AsyncBaseRepository):
    """
    Async repository for handling schedule operations.
    """

    async def get_by_office_id(self, office_id: UUID) -> Sequence[Schedule]:
        statement = select(Schedule).where(Schedule.office_id == office_id)
        result = await self.session.exec(statement)
        return result.all()

    async def delete_by_office_id(self, office_id: UUID) -> None:
        schedules = await self.get_by_office_id(office_id)
        for schedule in schedules:
            await self.session.delete(schedule)
        await self.session.commit()

    async def create_many(self, schedules: List[Schedule]) -> Sequence[Schedule]:
        for schedule in schedules:
            self.session.add(schedule)
        await self.session.commit()
        for schedule in schedules:
            await self.session.refresh(schedule)
        return schedules
