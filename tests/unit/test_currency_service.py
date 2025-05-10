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
