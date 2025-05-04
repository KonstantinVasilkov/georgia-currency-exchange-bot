"""
Tests for the repository classes.

This module contains tests for the repository classes, which are used to interact with the database.
"""

from datetime import datetime, timedelta, UTC

from src.db.repositories import OfficeRepository, OrganizationRepository, RateRepository


def test_organization_repository(db_session):
    """Test the OrganizationRepository class."""
    # Create a repository instance
    repo = OrganizationRepository(session=db_session)

    # Test create
    org_data = {
        "name": "Test Organization",
        "is_active": True,
        "description": "A test organization",
    }
    org = repo.create(org_data)
    assert org.id is not None
    assert org.name == "Test Organization"
    assert org.is_active is True
    assert org.description == "A test organization"

    # Test get
    retrieved_org = repo.get(org.id)
    assert retrieved_org is not None
    assert retrieved_org.id == org.id
    assert retrieved_org.name == org.name

    # Test update
    update_data = {
        "name": "Updated Organization",
        "description": "An updated description",
    }
    updated_org = repo.update(db_obj=org, obj_in=update_data)
    assert updated_org.id == org.id
    assert updated_org.name == "Updated Organization"
    assert updated_org.description == "An updated description"

    # Test get_active_organizations
    active_orgs = repo.get_active_organizations()
    assert len(active_orgs) == 1
    assert active_orgs[0].id == org.id

    # Test upsert (update existing)
    upsert_data = {"name": "Updated Organization", "website": "https://example.com"}
    upserted_org = repo.upsert(upsert_data)
    assert upserted_org.id == org.id
    assert upserted_org.website == "https://example.com"

    # Test upsert (create new)
    new_org_data = {"name": "New Organization", "is_active": True}
    new_org = repo.upsert(new_org_data)
    assert new_org.id != org.id
    assert new_org.name == "New Organization"

    # Test mark_inactive_if_not_in_list
    count = repo.mark_inactive_if_not_in_list([new_org.id])
    assert count == 1  # One organization should be marked as inactive

    # Verify the first organization is now inactive
    inactive_org = repo.get(org.id)
    assert inactive_org.is_active is False

    # Test delete
    deleted_org = repo.delete(id=new_org.id)
    assert deleted_org.id == new_org.id
    assert repo.get(new_org.id) is None


def test_office_repository(db_session):
    """Test the OfficeRepository class."""
    # Create a repository instance
    office_repo = OfficeRepository(session=db_session)
    org_repo = OrganizationRepository(session=db_session)

    # Create a test organization first
    org = org_repo.create({"name": "Test Organization", "is_active": True})

    # Test create
    office_data = {
        "name": "Test Office",
        "address": "123 Test St",
        "lat": 41.7151,
        "lng": 44.8271,
        "is_active": True,
        "organization_id": org.id,
    }
    office = office_repo.create(office_data)
    assert office.id is not None
    assert office.name == "Test Office"
    assert office.organization_id == org.id

    # Test get
    retrieved_office = office_repo.get(office.id)
    assert retrieved_office is not None
    assert retrieved_office.id == office.id
    assert retrieved_office.name == office.name

    # Test update
    update_data = {"name": "Updated Office", "address": "456 New St"}
    updated_office = office_repo.update(db_obj=office, obj_in=update_data)
    assert updated_office.id == office.id
    assert updated_office.name == "Updated Office"
    assert updated_office.address == "456 New St"

    # Test get_active_offices
    active_offices = office_repo.get_active_offices()
    assert len(active_offices) == 1
    assert active_offices[0].id == office.id

    # Test get_by_organization
    org_offices = office_repo.get_by_organization(org.id)
    assert len(org_offices) == 1
    assert org_offices[0].id == office.id

    # Test get_by_coordinates
    nearby_offices = office_repo.get_by_coordinates(41.7, 44.8, 20.0)
    assert len(nearby_offices) == 1
    assert nearby_offices[0].id == office.id

    # Test upsert (update existing)
    upsert_data = {
        "name": "Updated Office",
        "address": "789 Upsert St",
        "organization_id": org.id,
    }
    upserted_office = office_repo.upsert(upsert_data)
    assert upserted_office.id == office.id
    assert upserted_office.address == "789 Upsert St"

    # Test upsert (create new)
    new_office_data = {
        "name": "New Office",
        "address": "999 New St",
        "lat": 41.8,
        "lng": 44.9,
        "is_active": True,
        "organization_id": org.id,
    }
    new_office = office_repo.upsert(new_office_data)
    assert new_office.id != office.id
    assert new_office.name == "New Office"

    # Test mark_inactive_if_not_in_list
    count = office_repo.mark_inactive_if_not_in_list([new_office.id])
    assert count == 1  # One office should be marked as inactive

    # Verify the first office is now inactive
    inactive_office = office_repo.get(office.id)
    assert inactive_office.is_active is False

    # Test delete
    deleted_office = office_repo.delete(id=new_office.id)
    assert deleted_office.id == new_office.id
    assert office_repo.get(new_office.id) is None


def test_rate_repository(db_session):
    """Test the RateRepository class."""
    # Create repository instances
    rate_repo = RateRepository(session=db_session)
    office_repo = OfficeRepository(session=db_session)
    org_repo = OrganizationRepository(session=db_session)

    # Create a test organization and office first
    org = org_repo.create({"name": "Test Organization", "is_active": True})
    office = office_repo.create(
        {
            "name": "Test Office",
            "address": "123 Test St",
            "lat": 41.7151,
            "lng": 44.8271,
            "is_active": True,
            "organization_id": org.id,
        },
    )

    # Test create
    rate_data = {
        "office_id": office.id,
        "currency": "USD",
        "buy_rate": 2.65,
        "sell_rate": 2.70,
        "timestamp": datetime.now(tz=UTC),
    }
    rate = rate_repo.create(rate_data)
    assert rate.id is not None
    assert rate.office_id == office.id
    assert rate.currency == "USD"
    assert rate.buy_rate == 2.65
    assert rate.sell_rate == 2.70

    # Test get
    retrieved_rate = rate_repo.get(rate.id)
    assert retrieved_rate is not None
    assert retrieved_rate.id == rate.id
    assert retrieved_rate.currency == rate.currency

    # Test update
    update_data = {"buy_rate": 2.67, "sell_rate": 2.72}
    updated_rate = rate_repo.update(db_obj=rate, obj_in=update_data)
    assert updated_rate.id == rate.id
    assert updated_rate.buy_rate == 2.67
    assert updated_rate.sell_rate == 2.72

    # Test get_latest_rates
    latest_rates = rate_repo.get_latest_rates()
    assert len(latest_rates) == 1

    # Test get_latest_rates with filters
    usd_rates = rate_repo.get_latest_rates(currency="USD")
    assert len(usd_rates) == 1
    assert usd_rates[0].currency == "USD"

    office_rates = rate_repo.get_latest_rates(office_id=office.id)
    assert len(office_rates) == 1

    # Test get_rates_by_office
    office_rates = rate_repo.get_rates_by_office(office.id)
    assert len(office_rates) == 1

    # Test get_rates_by_currency
    usd_rates = rate_repo.get_rates_by_currency("USD")
    assert len(usd_rates) == 1
    assert usd_rates[0].currency == "USD"

    # Test get_best_rates
    best_buy_rates = rate_repo.get_best_rates("USD", buy=True)
    assert len(best_buy_rates) == 1
    assert best_buy_rates[0].currency == "USD"

    # Test upsert (update existing)
    upsert_data = {
        "office_id": office.id,
        "currency": "USD",
        "buy_rate": 2.68,
        "sell_rate": 2.73,
    }
    upserted_rate = rate_repo.upsert(upsert_data)
    assert upserted_rate.id == rate.id
    assert upserted_rate.buy_rate == 2.68
    assert upserted_rate.sell_rate == 2.73

    # Test upsert (create new)
    new_rate_data = {
        "office_id": office.id,
        "currency": "GBP",
        "buy_rate": 3.50,
        "sell_rate": 3.55,
    }
    new_rate = rate_repo.upsert(new_rate_data)
    assert new_rate.id != rate.id
    assert new_rate.currency == "GBP"

    # Test delete_old_rates
    # First, create an old rate
    old_timestamp = datetime.utcnow() - timedelta(hours=4)
    old_rate_data = {
        "office_id": office.id,
        "currency": "JPY",
        "buy_rate": 0.025,
        "sell_rate": 0.027,
        "timestamp": old_timestamp,
    }
    old_rate = rate_repo.create(old_rate_data)

    # Now delete old rates
    deleted_count = rate_repo.delete_old_rates(hours=3)
    assert deleted_count == 1  # One rate should be deleted

    # Verify the old rate is gone
    assert rate_repo.get(old_rate.id) is None

    # Test delete
    deleted_rate = rate_repo.delete(id=new_rate.id)
    assert deleted_rate.id == new_rate.id
    assert rate_repo.get(new_rate.id) is None
