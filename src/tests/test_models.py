import pytest
from sqlmodel import select
from src.db.models import Office, Organization, Rate

def test_models_exist():
    """
    Test that the models are correctly defined with the expected table names.
    """
    # Verify model table names
    assert Office.__tablename__ == "office"
    assert Organization.__tablename__ == "organization"
    assert Rate.__tablename__ == "rate"

def test_models_query(db_session):
    """
    Test that we can query the models using the database session.

    Args:
        db_session: SQLAlchemy session fixture from conftest.py
    """
    # Query all tables
    offices = db_session.exec(select(Office)).all()
    organizations = db_session.exec(select(Organization)).all()
    rates = db_session.exec(select(Rate)).all()

    # Initially, tables should be empty
    assert len(offices) == 0
    assert len(organizations) == 0
    assert len(rates) == 0

def test_models_create(db_session):
    """
    Test that we can create and query model instances.

    Args:
        db_session: SQLAlchemy session fixture from conftest.py
    """
    # Create a test organization
    org = Organization(name="Test Organization")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Verify the organization was created
    assert org.id is not None
    assert org.name == "Test Organization"

    # Create a test office
    office = Office(
        name="Test Office",
        address="123 Test St",
        lat=41.7151,
        lng=44.8271,
        organization_id=org.id
    )
    db_session.add(office)
    db_session.commit()
    db_session.refresh(office)

    # Verify the office was created
    assert office.id is not None
    assert office.name == "Test Office"
    assert office.organization_id == org.id

    # Create a test rate
    rate = Rate(
        office_id=office.id,
        currency="USD",
        buy_rate=2.65,
        sell_rate=2.70
    )
    db_session.add(rate)
    db_session.commit()
    db_session.refresh(rate)

    # Verify the rate was created
    assert rate.id is not None
    assert rate.office_id == office.id
    assert rate.currency == "USD"

    # Query the models to verify relationships
    db_org = db_session.get(Organization, org.id)
    assert db_org is not None
    assert len(db_org.offices) == 1
    assert db_org.offices[0].id == office.id

    db_office = db_session.get(Office, office.id)
    assert db_office is not None
    assert db_office.organization_id == org.id
    assert len(db_office.rates) == 1
    assert db_office.rates[0].id == rate.id
