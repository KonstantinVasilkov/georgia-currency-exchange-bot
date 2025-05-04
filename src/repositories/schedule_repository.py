"""
Repository for handling schedule operations.
"""

from typing import List, Sequence
from uuid import UUID

from sqlmodel import select

from src.db.models.schedule import Schedule
from src.db.repositories.base_repository import BaseRepository


class ScheduleRepository(BaseRepository):
    """
    Repository for handling schedule operations.
    """

    def get_by_office_id(self, office_id: UUID) -> Sequence[Schedule]:
        """
        Get all schedules for a specific office.

        Args:
            office_id: ID of the office

        Returns:
            List[Schedule]: List of schedules for the office
        """
        statement = select(Schedule).where(Schedule.office_id == office_id)
        return self.session.exec(statement).all()

    def delete_by_office_id(self, office_id: UUID) -> None:
        """
        Delete all schedules for a specific office.

        Args:
            office_id: ID of the office
        """
        schedules = self.get_by_office_id(office_id)
        for schedule in schedules:
            self.session.delete(schedule)
        self.session.commit()

    def create_many(self, schedules: List[Schedule]) -> Sequence[Schedule]:
        """
        Create multiple schedule entries.

        Args:
            schedules: List of schedule entries to create

        Returns:
            List[Schedule]: List of created schedule entries
        """
        for schedule in schedules:
            self.session.add(schedule)
        self.session.commit()
        for schedule in schedules:
            self.session.refresh(schedule)
        return schedules
