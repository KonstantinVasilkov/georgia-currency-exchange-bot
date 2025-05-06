"""
Rate repository for database operations.

This module provides a repository for Rate model operations.
"""

from sqlmodel import select

from src.repositories.base_repository import AsyncBaseRepository


class AsyncRateRepository(AsyncBaseRepository):
    """
    Async repository for Rate model operations.
    """

    async def get_latest_rates(self, limit: int = 10):
        statement = (
            select(self.model_class)
            .order_by(getattr(self.model_class, "timestamp").desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_by_organization(self, organization_id, limit: int = 10):
        statement = (
            select(self.model_class)
            .where(getattr(self.model_class, "organization_id") == organization_id)
            .order_by(getattr(self.model_class, "timestamp").desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def upsert(self, rate_data: dict):
        existing_rate = await self.find_one_by(
            office_id=rate_data.get("office_id"),
            currency=rate_data.get("currency"),
        )
        if existing_rate:
            return await self.update(db_obj=existing_rate, obj_in=rate_data)
        else:
            return await self.create(obj_in=rate_data)
