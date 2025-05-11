import pytest
from types import SimpleNamespace
from src.bot.routers.org import handle_organization_selection
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_handle_organization_selection_sends_offices_and_map_links(monkeypatch):
    class Office:
        def __init__(self, name, address, lat, lng):
            self.name = name
            self.address = address
            self.lat = lat
            self.lng = lng

    class Org:
        def __init__(self, id, name):
            self.id = id
            self.name = name

    org = Org(id=1, name="Test Bank")
    offices = [
        Office("Main Branch", "Rustaveli Ave. 7", 41.7151, 44.8271),
        Office("Vake Branch", "Chavchavadze Ave. 60", 41.7200, 44.8000),
    ]

    # Patch DB session and repositories
    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(
        "src.bot.routers.org.async_get_db_session", lambda: FakeSession()
    )
    org_repo = AsyncMock()
    org_repo.find_one_by = AsyncMock(return_value=org)
    office_repo = AsyncMock()
    office_repo.get_by_organization = AsyncMock(return_value=offices)
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOfficeRepository", lambda session: office_repo
    )
    sent_messages = {}

    class FakeMessage:
        async def edit_text(self, text, reply_markup=None, parse_mode=None):
            sent_messages["text"] = text
            sent_messages["reply_markup"] = reply_markup
            sent_messages["parse_mode"] = parse_mode

    callback = SimpleNamespace(data="org:Test Bank", message=FakeMessage())
    await handle_organization_selection(callback)
    text = sent_messages["text"]
    assert "Main Branch - Rustaveli Ave. 7" in text
    assert "Vake Branch - Chavchavadze Ave. 60" in text
    assert "Open all in Google Maps" in text
    assert "Open all in Apple Maps" in text
