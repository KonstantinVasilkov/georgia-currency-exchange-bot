from typing import Any, Sequence
from pydantic import BaseModel
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository


class RateRow(BaseModel):
    organization: str
    usd: float | None = None
    eur: float | None = None
    rub: float | None = None


class CurrencyService:
    """
    Service for fetching and formatting latest currency rates for the bot.
    """

    def __init__(
        self,
        organization_repo: AsyncOrganizationRepository,
        office_repo: AsyncOfficeRepository,
        rate_repo: AsyncRateRepository,
    ) -> None:
        self.organization_repo = organization_repo
        self.office_repo = office_repo
        self.rate_repo = rate_repo

    async def get_latest_rates_table(self) -> list[RateRow]:
        """
        Get the latest rates for NBG, online banks, and best from other organizations.
        Returns a list of RateRow for display in the bot.
        """
        # 1. NBG
        nbg_row = None
        nbg_org = await self.organization_repo.find_one_by(external_ref_id="NBG")
        if nbg_org and nbg_org.is_active:
            nbg_offices = await self.office_repo.get_by_organization(nbg_org.id)
            if nbg_offices:
                nbg_office = nbg_offices[0]
                nbg_rates = await self.rate_repo.get_rates_by_office(
                    nbg_office.id, limit=10
                )
                nbg_row = self._make_row(nbg_org.name, nbg_rates)
        if not nbg_row:
            nbg_row = RateRow(organization="NBG", usd=None, eur=None, rub=None)

        # 2. Online banks (fixed order)
        online_banks = [
            ("Bank of Georgia", "mBank"),
            ("TBC Bank", "TBC mobile"),
            ("Credo Bank", "MyCredo"),
        ]
        bank_rows = []
        shown_org_ids = set()
        for bank_name, bank_ref_name in online_banks:
            org = await self.organization_repo.find_one_by(name=bank_ref_name)
            row = None
            if org and org.is_active:
                shown_org_ids.add(org.id)
                offices = await self.office_repo.get_by_organization(org.id)
                if offices:
                    office = offices[0]
                    rates = await self.rate_repo.get_rates_by_office(
                        office.id, limit=10
                    )
                    row = self._make_row(org.name, rates)
            if not row:
                row = RateRow(organization=bank_name, usd=None, eur=None, rub=None)
            bank_rows.append(row)

        # 3. Best from other organizations (up to 6, sorted by USD rate desc, skip already shown orgs)
        all_orgs = await self.organization_repo.get_active_organizations()
        best_rows = []
        best_candidates = []
        for org in all_orgs:
            if org.external_ref_id in {
                "NBG",
                "bank_of_georgia",
                "tbc_bank",
                "credo_bank",
            }:
                continue
            if org.id in shown_org_ids:
                continue
            offices = await self.office_repo.get_by_organization(org.id)
            if offices:
                office = offices[0]
                rates = await self.rate_repo.get_rates_by_office(office.id, limit=10)
                row = self._make_row(org.name, rates)
                best_candidates.append(row)
        # Sort by USD rate descending, then by org name
        best_candidates.sort(
            key=lambda r: (r.usd if r.usd is not None else -float("inf")), reverse=True
        )
        best_rows = best_candidates[:6]

        # Compose result
        result = [nbg_row]
        result.extend(bank_rows)
        result.extend(best_rows)
        return result

    def _make_row(self, org_name: str, rates: Sequence[Any]) -> RateRow:
        usd = eur = rub = None
        for rate in rates:
            if rate.currency == "USD":
                usd = rate.buy_rate
            elif rate.currency == "EUR":
                eur = rate.buy_rate
            elif rate.currency == "RUB":
                rub = rate.buy_rate
        return RateRow(organization=org_name, usd=usd, eur=eur, rub=rub)
