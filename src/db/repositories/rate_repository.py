"""
Rate repository for database operations.

This module provides a repository for Rate model operations.
"""

from typing import List, Optional
import uuid
from sqlmodel import Session, select
from datetime import datetime, timedelta

from src.db.models.rate import Rate
from src.db.repositories.base_repository import BaseRepository


class RateRepository(BaseRepository[Rate]):
    """
    Repository for Rate model operations.

    This class extends the BaseRepository to provide specific operations for the Rate model.
    """

    def __init__(self):
        """Initialize the repository with the Rate model."""
        super().__init__(Rate)

    def get_latest_rates(self, session: Session, office_id: Optional[uuid.UUID] = None, currency: Optional[str] = None) -> List[Rate]:
        """
        Get the latest rates.

        Args:
            session: The database session.
            office_id: Optional filter by office ID.
            currency: Optional filter by currency.

        Returns:
            A list of the latest rates.
        """
        statement = select(Rate).order_by(Rate.timestamp.desc())

        if office_id:
            statement = statement.where(Rate.office_id == office_id)

        if currency:
            statement = statement.where(Rate.currency == currency)

        return session.exec(statement).all()

    def get_rates_by_office(self, session: Session, office_id: uuid.UUID) -> List[Rate]:
        """
        Get rates by office ID.

        Args:
            session: The database session.
            office_id: The ID of the office.

        Returns:
            A list of rates for the specified office.
        """
        statement = select(Rate).where(Rate.office_id == office_id).order_by(Rate.timestamp.desc())
        return session.exec(statement).all()

    def get_rates_by_currency(self, session: Session, currency: str) -> List[Rate]:
        """
        Get rates by currency.

        Args:
            session: The database session.
            currency: The currency code.

        Returns:
            A list of rates for the specified currency.
        """
        statement = select(Rate).where(Rate.currency == currency).order_by(Rate.timestamp.desc())
        return session.exec(statement).all()

    def get_best_rates(self, session: Session, currency: str, buy: bool = True) -> List[Rate]:
        """
        Get the best rates for a currency.

        Args:
            session: The database session.
            currency: The currency code.
            buy: If True, get the best buy rates (lowest). If False, get the best sell rates (highest).

        Returns:
            A list of rates sorted by the best rate.
        """
        statement = select(Rate).where(Rate.currency == currency)

        if buy:
            # For buy rates, lower is better
            statement = statement.order_by(Rate.buy_rate)
        else:
            # For sell rates, higher is better
            statement = statement.order_by(Rate.sell_rate.desc())

        return session.exec(statement).all()

    def delete_old_rates(self, session: Session, hours: int = 3) -> int:
        """
        Delete rates older than the specified number of hours.

        Args:
            session: The database session.
            hours: The number of hours to consider a rate as old.

        Returns:
            The number of rates deleted.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        statement = select(Rate).where(Rate.timestamp < cutoff_time)
        old_rates = session.exec(statement).all()

        for rate in old_rates:
            session.delete(rate)

        session.commit()
        return len(old_rates)

    def upsert(self, session: Session, rate_data: dict) -> Rate:
        """
        Create or update a rate.

        Args:
            session: The database session.
            rate_data: The rate data.

        Returns:
            The created or updated rate.
        """
        # Check if the rate exists by office_id and currency
        existing_rate = self.find_one_by(
            session,
            office_id=rate_data.get("office_id"),
            currency=rate_data.get("currency"),
        )

        if existing_rate:
            # Update existing rate
            return self.update(session, db_obj=existing_rate, obj_in=rate_data)
        else:
            # Create new rate
            return self.create(session, obj_in=rate_data)
