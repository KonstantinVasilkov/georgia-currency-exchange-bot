import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from aiogram.types import Message, Location, User
from src.bot.routers import currency
from src.bot.routers.org import handle_organization_selection, handle_find_office_by_org
from src.bot.routers.conversion import (
    handle_from_currency_selection,
    handle_to_currency_selection,
)
from src.bot.routers import location
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def clear_user_search_state():
    """Clear user_search_state before each test to avoid state leakage."""
    location.user_search_state.clear()
    yield
    location.user_search_state.clear()


@pytest.mark.asyncio
async def test_handle_main_menu(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup
        sent["parse_mode"] = parse_mode

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg)
    # Patch CurrencyService.get_latest_rates_table
    fake_rows = [
        type("Row", (), {"organization": "NBG", "usd": 2.5, "eur": 2.7, "rub": 0.03})(),
        type(
            "Row",
            (),
            {"organization": "BoG[online]", "usd": 2.51, "eur": 2.71, "rub": 0.031},
        )(),
        type(
            "Row",
            (),
            {"organization": "TBC[online]", "usd": 2.52, "eur": 2.72, "rub": 0.032},
        )(),
        type(
            "Row",
            (),
            {"organization": "Credo[online]", "usd": 2.53, "eur": 2.73, "rub": 0.033},
        )(),
    ]
    monkeypatch.setattr(
        currency.CurrencyService,
        "get_latest_rates_table",
        AsyncMock(return_value=fake_rows),
    )
    monkeypatch.setattr(
        currency, "AsyncOrganizationRepository", lambda session: AsyncMock()
    )
    monkeypatch.setattr(currency, "AsyncOfficeRepository", lambda session: AsyncMock())
    monkeypatch.setattr(
        currency, "AsyncRateRepository", lambda session, model_class=None: AsyncMock()
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(currency, "async_get_db_session", DummySession)
    callback.data = "main_menu"
    await currency.handle_main_menu(callback)
    assert "Organization" in sent["text"]
    assert "NBG" in sent["text"]
    assert sent["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_handle_best_rates(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="best_rates")
    await currency.handle_best_rates(callback)
    assert "Which currency do you want to sell?" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_sell_currency_selection(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="sell_currency:USD")
    await currency.handle_sell_currency_selection(callback)
    assert "Selected USD. What currency do you want to get?" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_get_currency_selection_no_sell_currency(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    msg.text = None  # Ensure .text attribute exists for isinstance check
    callback = SimpleNamespace(message=msg, data="get_currency:EUR")
    # Patch CurrencyService.get_best_rates_for_pair to return empty
    monkeypatch.setattr(
        currency.CurrencyService, "get_best_rates_for_pair", AsyncMock(return_value=[])
    )
    monkeypatch.setattr(
        currency, "AsyncOrganizationRepository", lambda session: AsyncMock()
    )
    monkeypatch.setattr(currency, "AsyncOfficeRepository", lambda session: AsyncMock())
    monkeypatch.setattr(
        currency, "AsyncRateRepository", lambda session, model_class=None: AsyncMock()
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(currency, "async_get_db_session", DummySession)
    await currency.handle_get_currency_selection(callback)
    assert "No rates available" in sent["text"]


@pytest.mark.asyncio
async def test_handle_find_office_menu(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup
        sent["parse_mode"] = parse_mode

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="find_office_menu")
    await location.handle_find_office_menu(callback)
    assert (
        "Find Nearest Office" in sent["text"]
        or "The first two options require you to share your location." in sent["text"]
    )
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_find_office_by_org(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="find_office_by_org")
    orgs = [type("Org", (), {"name": "TestOrg", "type": "Bank"})()]
    org_repo = AsyncMock()
    org_repo.get_active_organizations = AsyncMock(return_value=orgs)
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOrganizationRepository", lambda session: org_repo
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("src.bot.routers.org.async_get_db_session", DummySession)
    await handle_find_office_by_org(callback)
    assert "Select an organization" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_organization_selection_not_found(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="org:MissingOrg")
    org_repo = AsyncMock()
    org_repo.find_one_by = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOrganizationRepository", lambda session: org_repo
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("src.bot.routers.org.async_get_db_session", DummySession)
    await handle_organization_selection(callback)
    assert "not found" in sent["text"]


@pytest.mark.asyncio
async def test_handle_organization_selection_no_offices(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="org:TestOrg")
    org = type("Org", (), {"id": 1, "name": "TestOrg"})()
    org_repo = AsyncMock()
    org_repo.find_one_by = AsyncMock(return_value=org)
    office_repo = AsyncMock()
    office_repo.get_by_organization = AsyncMock(return_value=[])
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(
        "src.bot.routers.org.AsyncOfficeRepository", lambda session: office_repo
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr("src.bot.routers.org.async_get_db_session", DummySession)
    await handle_organization_selection(callback)
    assert "No offices found" in sent["text"]


@pytest.mark.asyncio
async def test_handle_find_nearest_office(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(
        message=msg, data="find_nearest_office", from_user=SimpleNamespace(id=1)
    )
    await location.handle_find_nearest_office(callback)
    assert (
        "Would you like to see only currently open offices or all offices?"
        in sent["text"]
    )
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_filter_open_only(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(
        message=msg, data="filter_open_only", from_user=SimpleNamespace(id=1)
    )
    await location.handle_filter_open_only(callback)
    assert "Please share your location" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_filter_all_offices(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(
        message=msg, data="filter_all_offices", from_user=SimpleNamespace(id=1)
    )
    await location.handle_filter_all_offices(callback)
    assert "Please share your location" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_location_message_no_user(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.reply.side_effect = reply
    msg.from_user = None
    msg.location = Location(latitude=41.7, longitude=44.8)
    await location.handle_location_message(msg)
    assert "Could not determine user or location." in sent["text"]


@pytest.mark.asyncio
async def test_handle_location_message_no_location(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.reply.side_effect = reply
    msg.from_user = SimpleNamespace(id=123)
    msg.location = None
    await location.handle_location_message(msg)
    assert "Could not determine user or location." in sent["text"]


@pytest.mark.asyncio
async def test_handle_location_message_no_state(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.reply.side_effect = reply
    msg.from_user = SimpleNamespace(id=123)
    msg.location = Location(latitude=41.7, longitude=44.8)
    location.user_search_state.pop(123, None)
    await location.handle_location_message(msg)
    assert "Session expired" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_from_currency_selection(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="from_currency:USD")
    monkeypatch.setattr(
        "src.bot.routers.conversion.get_currency_selection_keyboard",
        lambda *args, **kwargs: "keyboard",
    )
    monkeypatch.setattr(
        "src.bot.routers.conversion.AVAILABLE_CURRENCIES", ["USD", "EUR"]
    )
    await handle_from_currency_selection(callback)
    assert "Selected USD. Now select second currency:" in sent["text"]


@pytest.mark.asyncio
async def test_handle_to_currency_selection(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    msg.text = "Selected USD. Now select second currency:"
    callback = SimpleNamespace(message=msg, data="to_currency:EUR")
    monkeypatch.setattr(
        "src.bot.routers.conversion.get_back_to_main_menu_keyboard",
        lambda *args, **kwargs: "keyboard",
    )
    await handle_to_currency_selection(callback)
    assert "USD" in sent["text"]
    assert "EUR" in sent["text"]
    assert "Organization" in sent["text"]


@pytest.mark.asyncio
async def test_handle_find_best_rate_office(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(
        message=msg, data="find_best_rate_office", from_user=SimpleNamespace(id=1)
    )
    await location.handle_find_best_rate_office(callback)
    assert "currently open offices" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_find_best_sell_currency(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(
        message=msg, data="find_best_sell_currency:USD", from_user=SimpleNamespace(id=1)
    )
    await location.handle_find_best_sell_currency(callback)
    assert "Selected USD" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_find_best_get_currency(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    callback = SimpleNamespace(message=msg, data="find_best_get_currency:USD:GEL")
    await location.handle_find_best_get_currency(callback)
    assert (
        "Would you like to see only currently open offices or all offices?"
        in sent["text"]
    )
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_share_location(monkeypatch):
    sent = {}

    async def answer(text, reply_markup=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.answer.side_effect = answer
    callback = SimpleNamespace(message=msg, from_user=SimpleNamespace(id=1))
    monkeypatch.setattr(location, "ReplyKeyboardMarkup", lambda **kwargs: "keyboard")
    monkeypatch.setattr(location, "KeyboardButton", lambda **kwargs: None)

    async def dummy_answer():
        pass

    callback.answer = dummy_answer
    await location.handle_share_location(callback)
    assert "Please share your location" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_get_currency_selection_happy(monkeypatch):
    sent = {}

    async def edit_text(text, reply_markup=None, parse_mode=None):
        sent["text"] = text
        sent["reply_markup"] = reply_markup
        sent["parse_mode"] = parse_mode

    msg = AsyncMock(spec=Message)
    msg.edit_text.side_effect = edit_text
    msg.text = "Selected USD. What currency do you want to get?"
    msg.from_user = SimpleNamespace(id=1)  # Ensure from_user is set
    callback = SimpleNamespace(message=msg, data="get_currency:EUR")
    # Patch CurrencyService.get_best_rates_for_pair to return rates
    monkeypatch.setattr(
        currency.CurrencyService,
        "get_best_rates_for_pair",
        AsyncMock(return_value=[{"organization": "NBG", "rate": 2.5}]),
    )
    org = AsyncMock(id=1, name="NBG")
    office = Mock()
    office.id = 1
    office.name = "Main"
    office.lat = 0
    office.lng = 0
    office.organization = org
    org_repo = AsyncMock(find_one_by=AsyncMock(return_value=org))
    office_repo = AsyncMock(get_by_organization=AsyncMock(return_value=[office]))
    rate_mock = Mock()
    rate_mock.currency = "USD"
    rate_mock.buy_rate = 2.5
    rate_mock.sell_rate = 2.6
    rate_mock.timestamp = datetime.now(timezone.utc)
    rate_repo = AsyncMock(get_rates_by_office=AsyncMock(return_value=[rate_mock]))
    monkeypatch.setattr(
        currency, "AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(currency, "AsyncOfficeRepository", lambda session: office_repo)
    monkeypatch.setattr(
        currency, "AsyncRateRepository", lambda session, model_class=None: rate_repo
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(currency, "async_get_db_session", DummySession)
    # Set user_search_state for the test user to include sell_currency
    location.user_search_state[1] = {"sell_currency": "USD"}
    await currency.handle_get_currency_selection(callback)
    assert "NBG" in sent["text"]
    assert sent["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_handle_location_message_happy(monkeypatch):
    sent = {}

    async def answer(text, parse_mode=None, reply_markup=None):
        sent["text"] = text
        sent["parse_mode"] = parse_mode
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=321, is_bot=False, first_name="Test")
    msg.location = Location(latitude=41.7, longitude=44.8)
    msg.answer.side_effect = answer
    msg.reply = AsyncMock()
    # Patch all repos and services
    org = AsyncMock(id=1, name="NBG", type="Bank")
    office = Mock()
    office.id = 1
    office.name = "Main"
    office.address = "Addr"
    office.lat = 41.7
    office.lng = 44.8
    office.organization = org
    office_repo = AsyncMock(get_by_organization=AsyncMock(return_value=[office]))
    org_repo = AsyncMock(get_active_organizations=AsyncMock(return_value=[org]))
    rate_repo = AsyncMock(
        get_rates_by_office=AsyncMock(
            return_value=[AsyncMock(currency="USD", buy_rate=2.5, sell_rate=2.6)]
        )
    )
    monkeypatch.setattr(
        location, "AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(location, "AsyncOfficeRepository", lambda session: office_repo)
    monkeypatch.setattr(
        location, "AsyncRateRepository", lambda session, model_class=None: rate_repo
    )
    monkeypatch.setattr(location, "format_weekly_schedule", lambda s: "Mon-Fri: 9-18")
    location.user_search_state[321] = {"mode": "find_nearest_office"}
    await location.handle_location_message(msg)
    assert "🏢" in sent["text"]
    assert sent["reply_markup"] is not None


@pytest.mark.asyncio
async def test_handle_location_message_no_offices(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=322, is_bot=False, first_name="Test")
    msg.location = Location(latitude=41.7, longitude=44.8)
    msg.reply.side_effect = reply
    org_repo = AsyncMock(
        get_active_organizations=AsyncMock(
            return_value=[AsyncMock(id=1, name="NBG", type="Bank")]
        )
    )
    office_repo = AsyncMock(get_by_organization=AsyncMock(return_value=[]))
    monkeypatch.setattr(
        location, "AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(location, "AsyncOfficeRepository", lambda session: office_repo)

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(location, "async_get_db_session", DummySession)
    location.user_search_state[322] = {"mode": "find_nearest_office"}
    await location.handle_location_message(msg)
    assert "No offices found" in sent["text"]
    assert sent["reply_markup"] is None


@pytest.mark.asyncio
async def test_handle_location_message_no_open_offices(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=323, is_bot=False, first_name="Test")
    msg.location = Location(latitude=41.7, longitude=44.8)
    msg.reply.side_effect = reply
    org = AsyncMock(id=1, name="NBG", type="Bank")
    office = Mock()
    office.id = 1
    office.name = "Main"
    office.address = "Addr"
    office.lat = 41.7
    office.lng = 44.8
    office.organization = org
    office_repo = AsyncMock(get_by_organization=AsyncMock(return_value=[office]))
    org_repo = AsyncMock(get_active_organizations=AsyncMock(return_value=[org]))
    schedule_repo = AsyncMock(get_by_office_id=AsyncMock(return_value=[]))
    monkeypatch.setattr(
        location, "AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(location, "AsyncOfficeRepository", lambda session: office_repo)
    monkeypatch.setattr(
        location, "AsyncRateRepository", lambda session, model_class=None: AsyncMock()
    )
    monkeypatch.setattr(
        "src.repositories.schedule_repository.AsyncScheduleRepository",
        lambda *args, **kwargs: schedule_repo,
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def exec(self, statement):
            return AsyncMock()

    monkeypatch.setattr(location, "async_get_db_session", DummySession)
    location.user_search_state[323] = {"mode": "find_nearest_office", "open_only": True}
    await location.handle_location_message(msg)
    assert "No offices are currently open" in sent["text"]
    assert sent["reply_markup"] is None


@pytest.mark.asyncio
async def test_handle_location_message_no_best_rate_offices(monkeypatch):
    sent = {}

    async def reply(text, reply_markup=None, **kwargs):
        sent["text"] = text
        sent["reply_markup"] = reply_markup

    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=324, is_bot=False, first_name="Test")
    msg.location = Location(latitude=41.7, longitude=44.8)
    msg.reply.side_effect = reply
    org = AsyncMock(id=1, name="NBG", type="Bank")
    office = Mock()
    office.id = 1
    office.name = "Main"
    office.address = "Addr"
    office.lat = 41.7
    office.lng = 44.8
    office.organization = org
    office_repo = AsyncMock(get_by_organization=AsyncMock(return_value=[office]))
    org_repo = AsyncMock(get_active_organizations=AsyncMock(return_value=[org]))
    rate_repo = AsyncMock(get_rates_by_office=AsyncMock(return_value=[]))
    schedule_repo = AsyncMock(
        get_by_office_id=AsyncMock(
            return_value=[AsyncMock(day=0, opens_at=0, closes_at=1440)]
        )
    )
    monkeypatch.setattr(
        location, "AsyncOrganizationRepository", lambda session: org_repo
    )
    monkeypatch.setattr(location, "AsyncOfficeRepository", lambda session: office_repo)
    monkeypatch.setattr(
        location, "AsyncRateRepository", lambda session, model_class=None: rate_repo
    )
    monkeypatch.setattr(
        "src.repositories.schedule_repository.AsyncScheduleRepository",
        lambda *args, **kwargs: schedule_repo,
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def exec(self, statement):
            return AsyncMock()

    monkeypatch.setattr(location, "async_get_db_session", DummySession)
    location.user_search_state[324] = {"mode": "find_best_rate_office"}
    await location.handle_location_message(msg)
    assert "No offices with best rates found" in sent["text"]
    assert sent["reply_markup"] is None


@pytest.mark.asyncio
async def test_best_rates_between_scenario(monkeypatch):
    """
    Simulate user clicking best rates, picking two currencies, and bot replying with best rates table.
    """
    from src.bot.routers import conversion

    sent = {}

    # Step 1: User clicks 'best rates between currencies'
    async def edit_text_1(text, reply_markup=None, parse_mode=None):
        sent["step1_text"] = text
        sent["step1_reply_markup"] = reply_markup

    msg1 = AsyncMock(spec=Message)
    msg1.edit_text.side_effect = edit_text_1
    callback1 = SimpleNamespace(message=msg1, data="best_rates_between")
    await conversion.handle_best_rates_between(callback1)
    assert "Select first currency" in sent["step1_text"]
    assert sent["step1_reply_markup"] is not None

    # Step 2: User selects first currency
    async def edit_text_2(text, reply_markup=None, parse_mode=None):
        sent["step2_text"] = text
        sent["step2_reply_markup"] = reply_markup

    msg2 = AsyncMock(spec=Message)
    msg2.edit_text.side_effect = edit_text_2
    callback2 = SimpleNamespace(message=msg2, data="from_currency:USD")
    await conversion.handle_from_currency_selection(callback2)
    assert "Selected USD. Now select second currency:" in sent["step2_text"]
    assert sent["step2_reply_markup"] is not None

    # Step 3: User selects second currency
    async def edit_text_3(text, reply_markup=None, parse_mode=None):
        sent["step3_text"] = text
        sent["step3_reply_markup"] = reply_markup

    msg3 = AsyncMock(spec=Message)
    msg3.edit_text.side_effect = edit_text_3
    msg3.text = "Selected USD. Now select second currency:"
    callback3 = SimpleNamespace(message=msg3, data="to_currency:EUR")
    # Patch service to return known rates
    monkeypatch.setattr(
        conversion.CurrencyService,
        "get_best_rates_for_pair",
        AsyncMock(
            return_value=[
                {"organization": "NBG", "rate": 0.93},
                {"organization": "TBC Bank", "rate": 0.92},
            ]
        ),
    )
    # Patch repo/session dependencies
    monkeypatch.setattr(
        conversion, "AsyncOrganizationRepository", lambda session: AsyncMock()
    )
    monkeypatch.setattr(
        conversion, "AsyncOfficeRepository", lambda session: AsyncMock()
    )
    monkeypatch.setattr(
        conversion, "AsyncRateRepository", lambda session, model_class=None: AsyncMock()
    )

    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(conversion, "async_get_db_session", DummySession)
    await conversion.handle_to_currency_selection(callback3)
    assert "USD" in sent["step3_text"]
    assert "EUR" in sent["step3_text"]
    assert "NBG" in sent["step3_text"]
    assert "TBC Bank" in sent["step3_text"]
    assert sent["step3_reply_markup"] is not None
