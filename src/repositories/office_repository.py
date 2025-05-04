"""
Office repository for database operations.

This module provides a repository for Office model operations.
"""

from typing import List, Sequence
import uuid
from sqlalchemy import true
from sqlmodel import Session, select, col
from datetime import datetime

from src.db.models.office import Office
from src.db.repositories.base_repository import BaseRepository


class OfficeRepository(BaseRepository[Office]):
    """
    Repository for Office model operations.

    This class extends the BaseRepository to provide specific operations for the Office model.
    """

    def __init__(self, session: Session):
        """Initialize the repository with the Office model."""
        super().__init__(model_class=Office, session=session)

    def get_active_offices(self, skip: int = 0, limit: int = 100) -> Sequence[Office]:
        """
        Get active offices.

        Args:
            skip: The number of records to skip.
            limit: The maximum number of records to return.

        Returns:
            A list of active offices.
        """
        statement = (
            select(Office).where(Office.is_active == true()).offset(skip).limit(limit)
        )
        return self.session.exec(statement).all()

    def get_by_organization(self, organization_id: uuid.UUID) -> Sequence[Office]:
        """
        Get offices by organization ID.

        Args:
            organization_id: The ID of the organization.

        Returns:
            A list of offices belonging to the organization.
        """
        statement = select(Office).where(Office.organization_id == organization_id)
        return self.session.exec(statement).all()

    def get_by_coordinates(
        self, lat: float, lng: float, radius: float = 1.0
    ) -> Sequence[Office]:
        """
        Get offices near the specified coordinates.

        This is a simple implementation that finds offices within a square area.
        For more accurate distance calculations, a more complex formula would be needed.

        Args:
            lat: The latitude coordinate.
            lng: The longitude coordinate.
            radius: The radius in kilometers.

        Returns:
            A list of offices near the specified coordinates.
        """
        # Convert radius to approximate degrees (very rough approximation)
        # 1 degree of latitude is approximately 111 kilometers
        degree_radius = radius / 111.0

        statement = (
            select(Office)
            .where(Office.is_active == true())
            .where(Office.lat >= lat - degree_radius)
            .where(Office.lat <= lat + degree_radius)
            .where(Office.lng >= lng - degree_radius)
            .where(Office.lng <= lng + degree_radius)
        )
        return self.session.exec(statement).all()

    def mark_inactive_if_not_in_list(self, active_ids: List[uuid.UUID]) -> int:
        """
        Mark offices as inactive if their IDs are not in the provided list.

        Args:
            active_ids: List of IDs that should remain active.

        Returns:
            The number of offices marked as inactive.
        """
        if not active_ids:
            return 0

        statement = (
            select(Office)
            .where(Office.is_active == true())
            .where(col(Office.id).not_in(active_ids))
        )
        offices_to_deactivate = self.session.exec(statement).all()

        for office in offices_to_deactivate:
            office.is_active = False
            office.updated_at = datetime.utcnow()
            self.session.add(office)

        self.session.commit()
        return len(offices_to_deactivate)

    def upsert(self, office_data: dict) -> Office:
        """
        Create or update an office.

        Args:
            office_data: The office data.

        Returns:
            The created or updated office.
        """
        # Check if the office exists by name and organization_id
        existing_office = self.find_one_by(
            name=office_data.get("name"),
            organization_id=office_data.get("organization_id"),
        )

        if existing_office:
            # Update existing office
            office_data["updated_at"] = datetime.utcnow()
            return self.update(db_obj=existing_office, obj_in=office_data)
        else:
            # Create new office
            return self.create(obj_in=office_data)
