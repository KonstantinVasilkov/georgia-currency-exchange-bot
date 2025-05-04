"""
Organization repository for database operations.

This module provides a repository for Organization model operations.
"""

from typing import List, Sequence
import uuid
from sqlalchemy import true
from sqlmodel import Session, select, col
from datetime import datetime, UTC

from src.db.models.organization import Organization
from src.db.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    Repository for Organization model operations.

    This class extends the BaseRepository to provide specific operations for the Organization model.
    """

    def __init__(self, session: Session):
        """Initialize the repository with the Organization model."""
        super().__init__(model_class=Organization, session=session)

    def get_active_organizations(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[Organization]:
        """
        Get active organizations.

        Args:
            offset: The number of records to skip.
            limit: The maximum number of records to return.

        Returns:
            A list of active organizations.
        """
        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(statement).all()

    def mark_inactive_if_not_in_list(self, active_ids: List[uuid.UUID]) -> int:
        """
        Mark organizations as inactive if their IDs are not in the provided list.

        Args:
            active_ids: List of IDs that should remain active.

        Returns:
            The number of organizations marked as inactive.
        """
        if not active_ids:
            return 0

        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .where(col(Organization.id).not_in(active_ids))
        )
        orgs_to_deactivate = self.session.exec(statement).all()

        for org in orgs_to_deactivate:
            org.is_active = False
            org.updated_at = datetime.now(tz=UTC)
            self.session.add(org)

        self.session.commit()
        return len(orgs_to_deactivate)

    def upsert(self, org_data: dict) -> Organization:
        """
        Create or update an organization.

        Args:
            org_data: The organization data.

        Returns:
            The created or updated organization.
        """
        # Check if the organization exists by name
        existing_org = self.find_one_by(
            name=org_data.get("name"),
        )

        if existing_org:
            # Update existing organization
            org_data["updated_at"] = datetime.utcnow()
            return self.update(db_obj=existing_org, obj_in=org_data)
        else:
            # Create new organization
            return self.create(obj_in=org_data)

    def get_with_offices(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[Organization]:
        """
        Get organizations with their offices.

        Args:
            offset: The number of records to skip.
            limit: The maximum number of records to return.

        Returns:
            A list of organizations with their offices loaded.
        """
        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .offset(offset)
            .limit(limit)
        )
        organizations = self.session.exec(statement).all()

        # Load offices for each organization
        for org in organizations:
            # This will trigger the relationship loading
            _ = org.offices

        return organizations
