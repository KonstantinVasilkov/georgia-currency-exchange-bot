import pytest
import pytest_asyncio
from src.services.currency_service import CurrencyService
from unittest.mock import AsyncMock, MagicMock


@pytest_asyncio.fixture
def mock_repos():
    org_repo = AsyncMock()
    office_repo = AsyncMock()
    rate_repo = AsyncMock()
    return org_repo, office_repo, rate_repo


@pytest.mark.asyncio
async def test_get_latest_rates_table_full_scenario(mock_repos):
    org_repo, office_repo, rate_repo = mock_repos

    # Setup orgs
    def make_org(id, name, external_ref_id):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = True
        return org

    orgs = [
        make_org(1, "NBG", "NBG"),
        make_org(2, "BoG[online]", "bank_of_georgia"),
        make_org(3, "TBC[online]", "tbc_bank"),
        make_org(4, "Credo[online]", "credo_bank"),
        make_org(5, "BestOrg1", "best1"),
        make_org(6, "BestOrg2", "best2"),
    ]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (o for o in orgs if o.external_ref_id == kwargs.get("external_ref_id")), None
    )
    org_repo.get_active_organizations.return_value = orgs
    # Setup offices
    office_repo.get_by_organization.side_effect = lambda org_id: [MagicMock(id=org_id)]

    # Setup rates
    def make_rates(org_name):
        if org_name == "NBG":
            return [
                MagicMock(currency="USD", buy_rate=2.5),
                MagicMock(currency="EUR", buy_rate=3.0),
                MagicMock(currency="RUB", buy_rate=0.03),
            ]
        if org_name == "Bank of Georgia":
            return [
                MagicMock(currency="USD", buy_rate=2.6),
                MagicMock(currency="EUR", buy_rate=3.1),
                MagicMock(currency="RUB", buy_rate=0.031),
            ]
        if org_name == "TBC Bank":
            return [
                MagicMock(currency="USD", buy_rate=2.7),
                MagicMock(currency="EUR", buy_rate=3.2),
                MagicMock(currency="RUB", buy_rate=0.032),
            ]
        if org_name == "Credo Bank":
            return [
                MagicMock(currency="USD", buy_rate=2.8),
                MagicMock(currency="EUR", buy_rate=3.3),
                MagicMock(currency="RUB", buy_rate=0.033),
            ]
        if org_name == "BestOrg1":
            return [
                MagicMock(currency="USD", buy_rate=2.9),
                MagicMock(currency="EUR", buy_rate=3.4),
                MagicMock(currency="RUB", buy_rate=0.034),
            ]
        if org_name == "BestOrg2":
            return [
                MagicMock(currency="USD", buy_rate=2.4),
                MagicMock(currency="EUR", buy_rate=2.9),
                MagicMock(currency="RUB", buy_rate=0.029),
            ]
        return []

    rate_repo.get_rates_by_office.side_effect = lambda office_id, limit=10: make_rates(
        next(o.name for o in orgs if o.id == office_id)
    )
    service = CurrencyService(org_repo, office_repo, rate_repo)
    rows = await service.get_latest_rates_table()
    # Check order and content
    assert rows[0].organization == "NBG"
    assert rows[1].organization == "BoG[online]"
    assert rows[2].organization == "TBC[online]"
    assert rows[3].organization == "Credo[online]"
    assert rows[4].organization == "BestOrg1"
    assert rows[5].organization == "BestOrg2"
    assert rows[0].usd == 2.5 and rows[0].eur == 3.0 and rows[0].rub == 0.03
    assert rows[4].usd == 2.9 and rows[4].eur == 3.4 and rows[4].rub == 0.034


@pytest.mark.asyncio
async def test_get_latest_rates_table_missing_data(mock_repos):
    org_repo, office_repo, rate_repo = mock_repos

    # Only NBG is present and active
    def make_org(id, name, external_ref_id):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = True
        return org

    orgs = [make_org(1, "NBG", "NBG")]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (o for o in orgs if o.external_ref_id == kwargs.get("external_ref_id")), None
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.return_value = [MagicMock(id=1)]
    rate_repo.get_rates_by_office.return_value = []
    service = CurrencyService(org_repo, office_repo, rate_repo)
    rows = await service.get_latest_rates_table()
    # NBG row should be present, online banks should be present with None, no best others
    assert rows[0].organization == "NBG"
    assert rows[1].organization == "BoG[online]"
    assert rows[2].organization == "TBC[online]"
    assert rows[3].organization == "Credo[online]"
    assert all(r.usd is None and r.eur is None and r.rub is None for r in rows[1:4])
    assert len(rows) == 4


@pytest.mark.asyncio
async def test_get_best_rates_for_pair_usd_to_gel(mock_repos):
    org_repo, office_repo, rate_repo = mock_repos

    # Setup orgs
    def make_org(id, name, external_ref_id, org_type=None):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = True
        org.type = org_type
        return org

    orgs = [
        make_org(1, "National Bank of Georgia", "NBG"),
        make_org(2, "mBank", None, "Online"),
        make_org(3, "TBC mobile", None, "Online"),
        make_org(4, "MyCredo", None, "Online"),
        make_org(5, "BestOrg1", None),
        make_org(6, "BestOrg2", None),
    ]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (
            o
            for o in orgs
            if (
                kwargs.get("external_ref_id")
                and o.external_ref_id == kwargs.get("external_ref_id")
            )
            or (kwargs.get("name") and o.name == kwargs.get("name"))
        ),
        None,
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.side_effect = lambda org_id: [MagicMock(id=org_id)]

    # Setup rates: USD->GEL (buy_rate for USD, sell_rate for GEL)
    def make_rates(org_id):
        # All orgs have both USD and GEL
        return [
            MagicMock(
                currency="USD",
                buy_rate=2.5 + org_id * 0.1,
                sell_rate=2.6 + org_id * 0.1,
            ),
            MagicMock(currency="GEL", buy_rate=1.0, sell_rate=1.0),
        ]

    rate_repo.get_rates_by_office.side_effect = lambda office_id, limit=10: make_rates(
        office_id
    )

    service = CurrencyService(org_repo, office_repo, rate_repo)
    results = await service.get_best_rates_for_pair("USD", "GEL")

    # Check org names and mapping
    org_names = [r["organization"] for r in results]
    assert "National Bank of Georgia" in org_names
    assert "mBank" in org_names
    assert "TBC mobile" in org_names
    assert "MyCredo" in org_names
    # Check rates are correct (should be buy_rate for USD)
    for r in results:
        if r["organization"] == "National Bank of Georgia":
            assert abs(r["rate"] - 2.6) < 0.01
        if r["organization"] == "mBank":
            assert abs(r["rate"] - 2.7) < 0.01


@pytest.mark.asyncio
async def test_get_latest_rates_table_nbg_inactive(mock_repos) -> None:
    org_repo, office_repo, rate_repo = mock_repos

    def make_org(id: int, name: str, external_ref_id: str, is_active: bool = True):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = is_active
        return org

    orgs = [
        make_org(1, "NBG", "NBG", False),
        make_org(2, "BoG[online]", "bank_of_georgia"),
        make_org(3, "TBC[online]", "tbc_bank"),
        make_org(4, "Credo[online]", "credo_bank"),
    ]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (o for o in orgs if o.external_ref_id == kwargs.get("external_ref_id")), None
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.side_effect = lambda org_id: [MagicMock(id=org_id)]
    rate_repo.get_rates_by_office.return_value = []
    service = CurrencyService(org_repo, office_repo, rate_repo)
    rows = await service.get_latest_rates_table()
    assert rows[0].organization == "NBG"
    assert rows[0].usd is None and rows[0].eur is None and rows[0].rub is None


@pytest.mark.asyncio
async def test_get_latest_rates_table_online_banks_inactive(mock_repos) -> None:
    org_repo, office_repo, rate_repo = mock_repos

    def make_org(id: int, name: str, external_ref_id: str, is_active: bool = True):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = is_active
        return org

    orgs = [
        make_org(1, "NBG", "NBG"),
        make_org(2, "BoG[online]", "bank_of_georgia", False),
        make_org(3, "TBC[online]", "tbc_bank", False),
        make_org(4, "Credo[online]", "credo_bank", False),
    ]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (o for o in orgs if o.external_ref_id == kwargs.get("external_ref_id")), None
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.side_effect = lambda org_id: [MagicMock(id=org_id)]
    rate_repo.get_rates_by_office.return_value = []
    service = CurrencyService(org_repo, office_repo, rate_repo)
    rows = await service.get_latest_rates_table()
    assert rows[1].organization == "BoG[online]"
    assert rows[1].usd is None and rows[1].eur is None and rows[1].rub is None
    assert rows[2].organization == "TBC[online]"
    assert rows[2].usd is None and rows[2].eur is None and rows[2].rub is None
    assert rows[3].organization == "Credo[online]"
    assert rows[3].usd is None and rows[3].eur is None and rows[3].rub is None


@pytest.mark.asyncio
async def test_get_latest_rates_table_no_organizations(mock_repos) -> None:
    org_repo, office_repo, rate_repo = mock_repos
    org_repo.find_one_by.return_value = None
    org_repo.get_active_organizations.return_value = []
    office_repo.get_by_organization.return_value = []
    rate_repo.get_rates_by_office.return_value = []
    service = CurrencyService(org_repo, office_repo, rate_repo)
    rows = await service.get_latest_rates_table()
    assert rows[0].organization == "NBG"
    assert all(row.usd is None and row.eur is None and row.rub is None for row in rows)


@pytest.mark.asyncio
async def test_get_best_rates_for_pair_missing_rates(mock_repos) -> None:
    org_repo, office_repo, rate_repo = mock_repos

    def make_org(
        id: int,
        name: str,
        external_ref_id: str | None = None,
        org_type: str | None = None,
    ):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = True
        org.type = org_type
        return org

    orgs = [make_org(1, "National Bank of Georgia", "NBG")]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (
            o
            for o in orgs
            if (
                kwargs.get("external_ref_id")
                and o.external_ref_id == kwargs.get("external_ref_id")
            )
            or (kwargs.get("name") and o.name == kwargs.get("name"))
        ),
        None,
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.return_value = [MagicMock(id=1)]
    rate_repo.get_rates_by_office.return_value = []
    service = CurrencyService(org_repo, office_repo, rate_repo)
    results = await service.get_best_rates_for_pair("USD", "GEL")
    assert results == []


@pytest.mark.asyncio
async def test_get_best_rates_for_pair_cross_currency(mock_repos) -> None:
    org_repo, office_repo, rate_repo = mock_repos

    def make_org(
        id: int,
        name: str,
        external_ref_id: str | None = None,
        org_type: str | None = None,
    ):
        org = MagicMock(spec=[])
        org.id = id
        org.name = name
        org.external_ref_id = external_ref_id
        org.is_active = True
        org.type = org_type
        return org

    orgs = [make_org(1, "National Bank of Georgia", "NBG")]
    org_repo.find_one_by.side_effect = lambda **kwargs: next(
        (
            o
            for o in orgs
            if (
                kwargs.get("external_ref_id")
                and o.external_ref_id == kwargs.get("external_ref_id")
            )
            or (kwargs.get("name") and o.name == kwargs.get("name"))
        ),
        None,
    )
    org_repo.get_active_organizations.return_value = orgs
    office_repo.get_by_organization.return_value = [MagicMock(id=1)]
    # USD->EUR via GEL: buy_rate for USD, sell_rate for EUR
    rate_repo.get_rates_by_office.return_value = [
        MagicMock(currency="USD", buy_rate=2.5, sell_rate=2.6),
        MagicMock(currency="EUR", buy_rate=3.0, sell_rate=3.1),
        MagicMock(currency="GEL", buy_rate=1.0, sell_rate=1.0),
    ]
    service = CurrencyService(org_repo, office_repo, rate_repo)
    results = await service.get_best_rates_for_pair("USD", "EUR")
    assert results
    assert results[0]["organization"] == "National Bank of Georgia"
    # Should be 2.5 / 3.1
    assert abs(results[0]["rate"] - (2.5 / 3.1)) < 0.01
