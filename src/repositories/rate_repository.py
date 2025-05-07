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

    async def get_latest_rates(
        self, currency: str | None = None, office_id: str | None = None, limit: int = 10
    ):
        """
        Get latest rates, optionally filtered by currency and/or office_id.
        """
        statement = select(self.model_class)
        if currency is not None:
            statement = statement.where(
                getattr(self.model_class, "currency") == currency
            )
        if office_id is not None:
            statement = statement.where(
                getattr(self.model_class, "office_id") == office_id
            )
        statement = statement.order_by(
            getattr(self.model_class, "timestamp").desc()
        ).limit(limit)
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

    async def get_rates_by_office(self, office_id, limit: int = 10):
        """
        Get latest rates for a specific office.
        """
        statement = (
            select(self.model_class)
            .where(getattr(self.model_class, "office_id") == office_id)
            .order_by(getattr(self.model_class, "timestamp").desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_rates_by_currency(self, currency: str, limit: int = 10):
        """
        Get latest rates for a specific currency.
        """
        statement = (
            select(self.model_class)
            .where(getattr(self.model_class, "currency") == currency)
            .order_by(getattr(self.model_class, "timestamp").desc())
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def get_best_rates(self, currency: str, buy: bool = True, limit: int = 10):
        """
        Get best buy or sell rates for a currency.
        If buy=True, get highest buy_rate; else, get lowest sell_rate.
        """
        order_col = "buy_rate" if buy else "sell_rate"
        order_func = getattr(self.model_class, order_col)
        order_by = order_func.desc() if buy else order_func.asc()
        statement = (
            select(self.model_class)
            .where(getattr(self.model_class, "currency") == currency)
            .order_by(order_by)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def delete_old_rates(self, hours: int = 3) -> int:
        """
        Delete rates older than the specified number of hours.
        Returns the number of deleted rows.
        """
        from datetime import datetime, timedelta, UTC

        threshold = datetime.now(tz=UTC) - timedelta(hours=hours)
        statement = select(self.model_class).where(
            getattr(self.model_class, "timestamp") < threshold
        )
        old_rates = (await self.session.exec(statement)).all()
        count = 0
        for rate in old_rates:
            await self.session.delete(rate)
            count += 1
        await self.session.commit()
        return count
