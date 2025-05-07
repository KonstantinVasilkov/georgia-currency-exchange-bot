from sqlmodel import select
from src.db.models import Office, Organization, Rate
import pytest


def test_models_exist():
    """
    Test that the models are correctly defined with the expected table names.
    """
    # Verify model table names
    assert Office.__tablename__ == "office"
    assert Organization.__tablename__ == "organization"
    assert Rate.__tablename__ == "rate"


@pytest.mark.asyncio
async def test_models_query(db_session):
    """
    Test that we can query the models using the database session.

    Args:
        db_session: SQLAlchemy async session fixture from conftest.py
    """
    offices = (await db_session.exec(select(Office))).all()
    organizations = (await db_session.exec(select(Organization))).all()
    rates = (await db_session.exec(select(Rate))).all()
    assert isinstance(offices, list)
    assert isinstance(organizations, list)
    assert isinstance(rates, list)


@pytest.mark.asyncio
async def test_models_create(db_session):
    """
    Test that we can create and query model instances.

    Args:
        db_session: SQLAlchemy async session fixture from conftest.py
    """
    org = Organization(name="Test Organization")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    assert org.id is not None
    office = Office(
        name="Test Office",
        address="123 Test St",
        lat=1.0,
        lng=2.0,
        organization_id=org.id,
    )
    db_session.add(office)
    await db_session.commit()
    await db_session.refresh(office)
    assert office.id is not None
    rate = Rate(office_id=office.id, currency="USD", buy_rate=2.5, sell_rate=2.6)
    db_session.add(rate)
    await db_session.commit()
    await db_session.refresh(rate)
    assert rate.id is not None
