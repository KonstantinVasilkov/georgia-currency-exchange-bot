"""
Organization repository for database operations.

This module provides a repository for Organization model operations.
"""

from typing import List, Sequence
import uuid
from sqlalchemy import true
from sqlmodel import select, col
from datetime import datetime, UTC

from src.db.models.organization import Organization
from src.repositories.base_repository import AsyncBaseRepository


class AsyncOrganizationRepository(AsyncBaseRepository[Organization]):
    """
    Async repository for Organization model operations.
    """

    def __init__(self, session):
        super().__init__(model_class=Organization, session=session)

    async def get_active_organizations(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[Organization]:
        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def mark_inactive_if_not_in_list(self, active_ids: List[uuid.UUID]) -> int:
        if not active_ids:
            return 0
        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .where(col(Organization.id).not_in(active_ids))
        )
        orgs_to_deactivate = (await self.session.exec(statement)).all()
        for org in orgs_to_deactivate:
            org.is_active = False
            org.updated_at = datetime.now(tz=UTC)
            self.session.add(org)
        await self.session.commit()
        return len(orgs_to_deactivate)

    async def upsert(self, org_data: dict) -> Organization:
        existing_org = await self.find_one_by(name=org_data.get("name"))
        if existing_org:
            org_data["updated_at"] = datetime.utcnow()
            return await self.update(db_obj=existing_org, obj_in=org_data)
        else:
            return await self.create(obj_in=org_data)

    async def get_with_offices(
        self, offset: int = 0, limit: int = 100
    ) -> Sequence[Organization]:
        statement = (
            select(Organization)
            .where(Organization.is_active == true())
            .offset(offset)
            .limit(limit)
        )
        organizations = (await self.session.exec(statement)).all()
        for org in organizations:
            _ = org.offices
        return organizations
