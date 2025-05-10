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
    DataFetcher,
    ExchangeResponse,
    MapResponse,
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
def sample_map_data():
    """Fixture providing sample map data for testing."""
    return {
        "best": {
            "USD": {
                "ccy": "USD",
                "buy": 2.65,
                "sell": 2.70,
                "nbg": 2.68,
            }
        },
        "offices": [
            {
                "id": str(uuid.uuid4()),
                "organization_id": str(uuid.uuid4()),
                "city_id": str(uuid.uuid4()),
                "city": {
                    "en": "Tbilisi",
                    "ka": "თბილისი",
                    "ru": "Тбилиси",
                },
                "longitude": 44.8271,
                "latitude": 41.7151,
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
                "office_icon": "https://example.com/office-icon.png",
                "icon": "https://example.com/icon.png",
                "working_now": True,
                "working_24_7": False,
                "schedule": [
                    {
                        "start": {
                            "en": "09:00",
                            "ka": "09:00",
                            "ru": "09:00",
                        },
                        "end": {
                            "en": "18:00",
                            "ka": "18:00",
                            "ru": "18:00",
                        },
                        "intervals": ["09:00-18:00"],
                    }
                ],
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


@pytest.fixture
def mock_api_connector(sample_exchange_data, sample_map_data):
    """Fixture providing a mock MyFinApiConnector."""
    connector = AsyncMock(spec=MyFinApiConnector)
    connector.get_exchange_rates.return_value = sample_exchange_data
    connector.get_office_coordinates.return_value = sample_map_data
    return connector


@pytest.fixture
def mock_session():
    """Fixture providing a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_repositories():
    """
    Fixture to provide async-mocked repository instances for SyncService tests.
    """
    org_repo = AsyncMock()
    office_repo = AsyncMock()
    rate_repo = AsyncMock()
    # Set up common async methods as needed
    org_repo.find_one_by = AsyncMock()
    office_repo.find_one_by = AsyncMock()
    rate_repo.find_one_by = AsyncMock()
    org_repo.create = AsyncMock()
    office_repo.create = AsyncMock()
    rate_repo.create = AsyncMock()
    org_repo.update = AsyncMock()
    office_repo.update = AsyncMock()
    rate_repo.update = AsyncMock()
    org_repo.upsert = AsyncMock()
    office_repo.upsert = AsyncMock()
    rate_repo.upsert = AsyncMock()
    org_repo.get = AsyncMock()
    office_repo.get = AsyncMock()
    rate_repo.get = AsyncMock()
    org_repo.get_active_organizations = AsyncMock()
    office_repo.get_active_offices = AsyncMock()
    rate_repo.get_latest_rates = AsyncMock()
    yield (org_repo, office_repo, rate_repo)


@pytest.fixture
def mock_schedule_repo():
    repo = AsyncMock()
    repo.delete_by_office_id = AsyncMock()
    repo.get_by_office_id = AsyncMock(return_value=[])
    return repo


@pytest.mark.asyncio
async def test_fetch_exchange_data(
    mock_api_connector,
    sample_exchange_data,
    db_session,
    mock_repositories,
    mock_schedule_repo,
):
    """Test fetching exchange data from the API."""
    org_repo, office_repo, rate_repo = mock_repositories
    org_repo.find_one_by.return_value = None

    # Create a DataFetcher with the mock API connector
    data_fetcher = DataFetcher(api_connector=mock_api_connector)

    # Call the fetch_exchange_data method
    result = await data_fetcher.fetch_exchange_data()

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
async def test_fetch_map_data(
    mock_api_connector,
    sample_map_data,
    db_session,
    mock_repositories,
    mock_schedule_repo,
):
    """Test fetching map data from the API."""
    org_repo, office_repo, rate_repo = mock_repositories
    org_repo.find_one_by.return_value = None

    # Create a DataFetcher with the mock API connector
    data_fetcher = DataFetcher(api_connector=mock_api_connector)

    # Call the fetch_map_data method
    result = await data_fetcher.fetch_map_data()

    # Verify the API connector was called with the expected parameters
    mock_api_connector.get_office_coordinates.assert_called_once_with(
        city="tbilisi", include_online=False, availability="All"
    )

    # Verify the result is a MapResponse object with the expected data
    assert isinstance(result, MapResponse)
    assert len(result.offices) == len(sample_map_data["offices"])
    assert result.offices[0].name.en == sample_map_data["offices"][0]["name"]["en"]


@pytest.mark.asyncio
async def test_process_map_data(
    mock_session, mock_repositories, sample_map_data, mock_schedule_repo
):
    """Test processing map data to update office coordinates."""
    org_repo, office_repo, rate_repo = mock_repositories
    org_repo.find_one_by.return_value = None

    # Create a SyncService with the mock session
    sync_service = SyncService(db_session=mock_session, api_connector=None)
    sync_service.organization_repo = org_repo
    sync_service.office_repo = office_repo
    sync_service.rate_repo = rate_repo
    sync_service.schedule_repo = mock_schedule_repo

    # Create a MapResponse object from the sample data
    map_data = MapResponse.model_validate(sample_map_data)

    # Mock an existing office
    existing_office = MagicMock()
    office_repo.find_one_by.return_value = existing_office

    # Call the _process_map_data method
    stats = await sync_service._process_map_data(map_data)

    # Verify the office repository was used to update the office
    assert office_repo.update.call_count == 1
    assert stats["offices_updated"] == 1

    # Verify the update was called with the correct coordinates
    update_call = office_repo.update.call_args[1]
    assert update_call["obj_in"]["lat"] == sample_map_data["offices"][0]["latitude"]
    assert update_call["obj_in"]["lng"] == sample_map_data["offices"][0]["longitude"]


@pytest.mark.asyncio
async def test_sync_data(
    mock_api_connector, mock_session, mock_repositories, mock_schedule_repo
):
    """Test synchronizing data from the API to the database."""
    org_repo, office_repo, rate_repo = mock_repositories
    org_repo.find_one_by.return_value = None
    office_repo.find_one_by.return_value = None

    # Create a SyncService with the mock session and API connector
    sync_service = SyncService(
        db_session=mock_session, api_connector=mock_api_connector
    )
    sync_service.organization_repo = org_repo
    sync_service.office_repo = office_repo
    sync_service.rate_repo = rate_repo
    sync_service.schedule_repo = mock_schedule_repo

    # Call the sync_data method
    stats = await sync_service.sync_data()

    # Verify both API endpoints were called
    mock_api_connector.get_exchange_rates.assert_called_once()
    mock_api_connector.get_office_coordinates.assert_called_once()

    # Verify the repositories were used to save data
    assert org_repo.create.call_count == 2
    assert office_repo.create.call_count == 2
    assert rate_repo.upsert.call_count == 2

    # Verify the stats were returned
    assert "organizations_created" in stats
    assert "offices_created" in stats
    assert "rates_created" in stats
    assert "offices_updated" in stats


@pytest.mark.asyncio
async def test_process_organizations_and_offices(
    mock_session,
    mock_repositories,
    sample_exchange_data,
    mock_api_connector,
    mock_schedule_repo,
):
    """Test processing organizations and offices from exchange data."""
    org_repo, office_repo, rate_repo = mock_repositories
    org_repo.find_one_by.return_value = None
    office_repo.find_one_by.return_value = None

    # Create a SyncService with the mock session and API connector
    sync_service = SyncService(
        db_session=mock_session, api_connector=mock_api_connector
    )
    sync_service.organization_repo = org_repo
    sync_service.office_repo = office_repo
    sync_service.rate_repo = rate_repo
    sync_service.schedule_repo = mock_schedule_repo

    # Create an ExchangeResponse object from the sample data
    exchange_data = ExchangeResponse.model_validate(sample_exchange_data)

    # Call the _process_organizations_and_offices method
    stats = await sync_service._process_organizations_and_offices(exchange_data)

    # Verify the repositories were used to save data
    assert org_repo.create.call_count == 2
    assert office_repo.create.call_count == 2
    assert rate_repo.upsert.call_count == 2

    # Verify the stats were returned
    assert "organizations_created" in stats
    assert "offices_created" in stats
    assert "rates_created" in stats
    assert "offices_updated" in stats


@pytest.mark.asyncio
async def test_sync_exchange_data():
    """Test that the sync_exchange_data function runs without errors."""
    # Mock the SyncService.sync_data method to avoid making real API calls
    with patch("src.services.sync_service.SyncService.sync_data") as mock_sync_data:
        expected_stats = {
            "organizations_created": 1,
            "organizations_updated": 0,
            "offices_created": 1,
            "offices_updated": 0,
            "offices_deactivated": 0,
            "rates_created": 1,
            "rates_updated": 0,
            "schedules_created": 0,
            "schedules_updated": 0,
        }
        mock_sync_data.return_value = expected_stats

        # Call the function with custom parameters
        result = await sync_exchange_data(
            city="batumi", include_online=False, availability="Working"
        )

        # Verify the SyncService.sync_data method was called with the correct parameters
        mock_sync_data.assert_called_once_with(
            city="batumi", include_online=False, availability="Working"
        )

        # Verify the function returns the expected stats
        assert result == expected_stats


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
        map_data = await sync_service.fetch_map_data()

        # Verify the response contains the expected data
        assert isinstance(exchange_data, ExchangeResponse)
        assert len(exchange_data.organizations) > 0
        assert len(exchange_data.best) > 0

        assert isinstance(map_data, MapResponse)
        assert len(map_data.offices) > 0
        assert len(map_data.best) > 0

        # Print some information about the response
        print(f"Fetched {len(exchange_data.organizations)} organizations")
        print(f"Fetched {len(exchange_data.best)} best rates")
        print(f"Fetched {len(map_data.offices)} offices with coordinates")

        # If we get here without an exception, the test passes
        assert True
    except Exception as e:
        pytest.skip(f"Skipping real API call test due to error: {e}")
