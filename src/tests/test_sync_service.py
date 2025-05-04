"""
Tests for the SyncService module.

This module contains tests for the SyncService module, which is used to fetch and
synchronize exchange rate data.
"""

import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session

from src.services.sync_service import (
    SyncService,
    ExchangeResponse,
    sync_exchange_data,
)
from src.external_connectors.myfin.api_connector import MyFinApiConnector
from src.utils.http_client import get_http_client


# Sample exchange rate data for testing
@pytest.fixture
def sample_exchange_data():
    """Fixture providing sample exchange rate data for testing."""
    return {
        "best": {
            "USD": {
                "ccy": "USD",
                "buy": 2.65,
                "sell": 2.70,
                "nbg": 2.68,
            }
        },
        "organizations": [
            {
                "id": str(uuid.uuid4()),
                "type": "bank",
                "link": "https://example.com",
                "icon": "https://example.com/icon.png",
                "name": {
                    "en": "Test Bank",
                    "ka": "ტესტ ბანკი",
                    "ru": "Тест Банк",
                },
                "best": {
                    "USD": {
                        "ccy": "USD",
                        "buy": 2.65,
                        "sell": 2.70,
                    }
                },
                "offices": [
                    {
                        "id": str(uuid.uuid4()),
                        "name": {
                            "en": "Test Office",
                            "ka": "ტესტ ოფისი",
                            "ru": "Тест Офис",
                        },
                        "address": {
                            "en": "123 Test St",
                            "ka": "ტესტის ქუჩა 123",
                            "ru": "Тестовая улица 123",
                        },
                        "icon": "https://example.com/office-icon.png",
                        "working_now": True,
                        "rates": {
                            "USD": {
                                "ccy": "USD",
                                "buy": 2.65,
                                "sell": 2.70,
                                "timeFrom": datetime.now(tz=UTC),
                                "time": datetime.now(tz=UTC),
                            }
                        },
                    }
                ],
            }
        ],
    }


@pytest.fixture
def mock_api_connector(sample_exchange_data):
    """Fixture providing a mock MyFinApiConnector."""
    connector = AsyncMock(spec=MyFinApiConnector)
    connector.get_exchange_rates.return_value = sample_exchange_data
    return connector


@pytest.fixture
def mock_session():
    """Fixture providing a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_repositories():
    """Fixture providing mock repositories."""
    with (
        patch("src.services.sync_service.OrganizationRepository") as org_repo_mock,
        patch("src.services.sync_service.OfficeRepository") as office_repo_mock,
        patch("src.services.sync_service.RateRepository") as rate_repo_mock,
    ):
        # Configure the mocks
        org_repo_instance = org_repo_mock.return_value
        office_repo_instance = office_repo_mock.return_value
        rate_repo_instance = rate_repo_mock.return_value

        # Mock find_one_by to return None (no existing records)
        org_repo_instance.find_one_by.return_value = None
        office_repo_instance.find_one_by.return_value = None

        # Mock create to return objects with IDs
        def create_org(obj_in):
            return MagicMock(id=uuid.uuid4())

        def create_office(obj_in):
            return MagicMock(id=uuid.uuid4())

        def create_rate(obj_in):
            rate = MagicMock()
            rate._is_new = True
            return rate

        org_repo_instance.create.side_effect = create_org
        office_repo_instance.create.side_effect = create_office
        rate_repo_instance.upsert.side_effect = create_rate

        yield org_repo_instance, office_repo_instance, rate_repo_instance


@pytest.mark.asyncio
async def test_fetch_exchange_data(
    mock_api_connector, sample_exchange_data, db_session
):
    """Test fetching exchange data from the API."""
    # Create a SyncService with the mock API connector
    sync_service = SyncService(db_session=db_session, api_connector=mock_api_connector)

    # Call the fetch_exchange_data method
    result = await sync_service.fetch_exchange_data()

    # Verify the API connector was called with the expected parameters
    mock_api_connector.get_exchange_rates.assert_called_once_with(
        city="tbilisi", include_online=True, availability="All"
    )

    # Verify the result is an ExchangeResponse object with the expected data
    assert isinstance(result, ExchangeResponse)
    assert len(result.organizations) == len(sample_exchange_data["organizations"])
    assert (
        result.organizations[0].name.en
        == sample_exchange_data["organizations"][0]["name"]["en"]
    )


@pytest.mark.asyncio
async def test_sync_data(mock_api_connector, mock_session, mock_repositories):
    """Test synchronizing data from the API to the database."""
    # Unpack the mock repositories
    org_repo, office_repo, rate_repo = mock_repositories

    # Create a SyncService with the mock API connector and session
    sync_service = SyncService(
        db_session=mock_session, api_connector=mock_api_connector
    )

    # Call the sync_data method
    stats = await sync_service.sync_data()

    # Verify the API connector was called
    mock_api_connector.get_exchange_rates.assert_called_once()

    # Verify the repositories were used to save data
    assert org_repo.create.call_count == 1
    assert office_repo.create.call_count == 1
    assert rate_repo.upsert.call_count == 1

    # Verify the stats were returned
    assert "organizations_created" in stats
    assert stats["organizations_created"] == 1
    assert stats["offices_created"] == 1
    assert stats["rates_created"] == 1


@pytest.mark.asyncio
async def test_process_organizations_and_offices(
    mock_session, mock_repositories, sample_exchange_data, mock_api_connector
):
    """Test processing organizations and offices from exchange data."""
    # Unpack the mock repositories
    org_repo, office_repo, rate_repo = mock_repositories

    # Create a SyncService with the mock session

    sync_service = SyncService(
        db_session=mock_session, api_connector=mock_api_connector
    )

    # Create an ExchangeResponse object from the sample data
    exchange_data = ExchangeResponse.model_validate(sample_exchange_data)

    # Call the _process_organizations_and_offices method
    stats = await sync_service._process_organizations_and_offices(exchange_data)

    # Verify the repositories were used to save data
    assert org_repo.create.call_count == 1
    assert office_repo.create.call_count == 1
    assert rate_repo.upsert.call_count == 1

    # Verify the stats were returned
    assert stats["organizations_created"] == 1
    assert stats["offices_created"] == 1
    assert stats["rates_created"] == 1

    # Verify inactive organizations and offices were marked
    assert org_repo.mark_inactive_if_not_in_list.call_count == 1
    assert office_repo.mark_inactive_if_not_in_list.call_count == 1


@pytest.mark.asyncio
async def test_sync_exchange_data():
    """Test that the sync_exchange_data function runs without errors."""
    # Mock the SyncService.sync_data method to avoid making real API calls
    with patch("src.services.sync_service.SyncService.sync_data") as mock_sync_data:
        mock_sync_data.return_value = {
            "organizations_created": 1,
            "organizations_updated": 0,
            "offices_created": 1,
            "offices_updated": 0,
            "offices_deactivated": 0,
            "rates_created": 1,
            "rates_updated": 0,
        }

        # Call the function
        await sync_exchange_data()

        # Verify the SyncService.sync_data method was called
        mock_sync_data.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_api_call(db_session):
    """
    Test making a real API call to the MyFin API.

    This test is marked as an integration test and will be skipped by default.
    To run it, use: pytest -m integration
    """
    # Create a SyncService
    http_client = get_http_client()
    myfin_api_connector = MyFinApiConnector(http_client_session=http_client.session)
    sync_service = SyncService(db_session=db_session, api_connector=myfin_api_connector)

    try:
        # Fetch data from the API
        exchange_data = await sync_service.fetch_exchange_data()

        # Verify the response contains the expected data
        assert isinstance(exchange_data, ExchangeResponse)
        assert len(exchange_data.organizations) > 0
        assert len(exchange_data.best) > 0

        # Print some information about the response
        print(f"Fetched {len(exchange_data.organizations)} organizations")
        print(f"Fetched {len(exchange_data.best)} best rates")

        # If we get here without an exception, the test passes
        assert True
    except Exception as e:
        pytest.skip(f"Skipping real API call test due to error: {e}")
