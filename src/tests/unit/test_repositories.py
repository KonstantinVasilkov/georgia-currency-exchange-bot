"""
Tests for the repository classes.

This module contains tests for the repository classes, which are used to interact with the database.
"""

from datetime import datetime, timedelta, UTC
import pytest
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.db.models.rate import Rate


@pytest.mark.asyncio
async def test_organization_repository(db_session):
    """Test the AsyncOrganizationRepository class."""
    repo = AsyncOrganizationRepository(session=db_session)

    org_data = {
        "name": "Test Organization",
        "is_active": True,
        "description": "A test organization",
    }
    org = await repo.create(org_data)
    assert org.id is not None
    assert org.name == "Test Organization"
    assert org.is_active is True
    assert org.description == "A test organization"

    retrieved_org = await repo.get(org.id)
    assert retrieved_org is not None
    assert retrieved_org.id == org.id
    assert retrieved_org.name == org.name

    update_data = {
        "name": "Updated Organization",
        "description": "An updated description",
    }
    updated_org = await repo.update(db_obj=org, obj_in=update_data)
    assert updated_org.id == org.id
    assert updated_org.name == "Updated Organization"
    assert updated_org.description == "An updated description"

    active_orgs = await repo.get_active_organizations()
    assert len(active_orgs) == 1
    assert active_orgs[0].id == org.id

    upsert_data = {"name": "Updated Organization", "website": "https://example.com"}
    upserted_org = await repo.upsert(upsert_data)
    assert upserted_org.id == org.id
    assert upserted_org.website == "https://example.com"

    new_org_data = {"name": "New Organization", "is_active": True}
    new_org = await repo.upsert(new_org_data)
    assert new_org.id != org.id
    assert new_org.name == "New Organization"

    count = await repo.mark_inactive_if_not_in_list([new_org.id])
    assert count == 1

    inactive_org = await repo.get(org.id)
    assert inactive_org.is_active is False

    deleted_org = await repo.delete(id=new_org.id)
    assert deleted_org.id == new_org.id
    assert await repo.get(new_org.id) is None


@pytest.mark.asyncio
async def test_office_repository(db_session):
    """Test the AsyncOfficeRepository class."""
    office_repo = AsyncOfficeRepository(session=db_session)
    org_repo = AsyncOrganizationRepository(session=db_session)

    org = await org_repo.create({"name": "Test Organization", "is_active": True})

    office_data = {
        "name": "Test Office",
        "address": "123 Test St",
        "lat": 41.7151,
        "lng": 44.8271,
        "is_active": True,
        "organization_id": org.id,
    }
    office = await office_repo.create(office_data)
    assert office.id is not None
    assert office.name == "Test Office"
    assert office.organization_id == org.id

    retrieved_office = await office_repo.get(office.id)
    assert retrieved_office is not None
    assert retrieved_office.id == office.id
    assert retrieved_office.name == office.name

    update_data = {"name": "Updated Office", "address": "456 New St"}
    updated_office = await office_repo.update(db_obj=office, obj_in=update_data)
    assert updated_office.id == office.id
    assert updated_office.name == "Updated Office"
    assert updated_office.address == "456 New St"

    active_offices = await office_repo.get_active_offices()
    assert len(active_offices) == 1
    assert active_offices[0].id == office.id

    org_offices = await office_repo.get_by_organization(org.id)
    assert len(org_offices) == 1
    assert org_offices[0].id == office.id

    nearby_offices = await office_repo.get_by_coordinates(41.7, 44.8, 20.0)
    assert len(nearby_offices) == 1
    assert nearby_offices[0].id == office.id

    upsert_data = {
        "name": "Updated Office",
        "address": "789 Upsert St",
        "organization_id": org.id,
    }
    upserted_office = await office_repo.upsert(upsert_data)
    assert upserted_office.id == office.id
    assert upserted_office.address == "789 Upsert St"

    new_office_data = {
        "name": "New Office",
        "address": "999 New St",
        "lat": 41.8,
        "lng": 44.9,
        "is_active": True,
        "organization_id": org.id,
    }
    new_office = await office_repo.upsert(new_office_data)
    assert new_office.id != office.id
    assert new_office.name == "New Office"

    count = await office_repo.mark_inactive_if_not_in_list([new_office.id])
    assert count == 1

    inactive_office = await office_repo.get(office.id)
    assert inactive_office.is_active is False

    deleted_office = await office_repo.delete(id=new_office.id)
    assert deleted_office.id == new_office.id
    assert await office_repo.get(new_office.id) is None


@pytest.mark.asyncio
async def test_rate_repository(db_session):
    """Test the AsyncRateRepository class."""
    rate_repo = AsyncRateRepository(session=db_session, model_class=Rate)
    office_repo = AsyncOfficeRepository(session=db_session)
    org_repo = AsyncOrganizationRepository(session=db_session)

    org = await org_repo.create({"name": "Test Organization", "is_active": True})
    office = await office_repo.create(
        {
            "name": "Test Office",
            "address": "123 Test St",
            "lat": 41.7151,
            "lng": 44.8271,
            "is_active": True,
            "organization_id": org.id,
        },
    )

    rate_data = {
        "office_id": office.id,
        "currency": "USD",
        "buy_rate": 2.65,
        "sell_rate": 2.70,
        "timestamp": datetime.now(tz=UTC),
    }
    rate = await rate_repo.create(rate_data)
    assert rate.id is not None
    assert rate.office_id == office.id
    assert rate.currency == "USD"
    assert rate.buy_rate == 2.65
    assert rate.sell_rate == 2.70

    retrieved_rate = await rate_repo.get(rate.id)
    assert retrieved_rate is not None
    assert retrieved_rate.id == rate.id
    assert retrieved_rate.currency == rate.currency

    update_data = {"buy_rate": 2.67, "sell_rate": 2.72}
    updated_rate = await rate_repo.update(db_obj=rate, obj_in=update_data)
    assert updated_rate.id == rate.id
    assert updated_rate.buy_rate == 2.67
    assert updated_rate.sell_rate == 2.72

    latest_rates = await rate_repo.get_latest_rates()
    assert len(latest_rates) == 1

    usd_rates = await rate_repo.get_latest_rates(currency="USD")
    assert len(usd_rates) == 1
    assert usd_rates[0].currency == "USD"

    office_rates = await rate_repo.get_latest_rates(office_id=office.id)
    assert len(office_rates) == 1

    office_rates = await rate_repo.get_rates_by_office(office.id)
    assert len(office_rates) == 1

    usd_rates = await rate_repo.get_rates_by_currency("USD")
    assert len(usd_rates) == 1
    assert usd_rates[0].currency == "USD"

    best_buy_rates = await rate_repo.get_best_rates("USD", buy=True)
    assert len(best_buy_rates) == 1
    assert best_buy_rates[0].currency == "USD"

    upsert_data = {
        "office_id": office.id,
        "currency": "USD",
        "buy_rate": 2.68,
        "sell_rate": 2.73,
    }
    upserted_rate = await rate_repo.upsert(upsert_data)
    assert upserted_rate.id == rate.id
    assert upserted_rate.buy_rate == 2.68
    assert upserted_rate.sell_rate == 2.73

    new_rate_data = {
        "office_id": office.id,
        "currency": "GBP",
        "buy_rate": 3.50,
        "sell_rate": 3.55,
    }
    new_rate = await rate_repo.upsert(new_rate_data)
    assert new_rate.id != rate.id
    assert new_rate.currency == "GBP"

    old_timestamp = datetime.utcnow() - timedelta(hours=4)
    old_rate_data = {
        "office_id": office.id,
        "currency": "JPY",
        "buy_rate": 0.025,
        "sell_rate": 0.027,
        "timestamp": old_timestamp,
    }
    old_rate = await rate_repo.create(old_rate_data)

    deleted_count = await rate_repo.delete_old_rates(hours=3)
    assert deleted_count == 1

    assert await rate_repo.get(old_rate.id) is None

    deleted_rate = await rate_repo.delete(id=new_rate.id)
    assert deleted_rate.id == new_rate.id
    assert await rate_repo.get(new_rate.id) is None
