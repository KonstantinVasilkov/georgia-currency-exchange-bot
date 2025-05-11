from typing import Any, Sequence, TypedDict
from pydantic import BaseModel
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository


class RateRow(BaseModel):
    organization: str
    usd: float | None = None
    eur: float | None = None
    rub: float | None = None


class BestRateResult(TypedDict):
    organization: str
    rate: float


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
                nbg_row = self._make_row("NBG", nbg_rates)
        if not nbg_row:
            nbg_row = RateRow(organization="NBG", usd=None, eur=None, rub=None)

        # 2. Online banks (fixed order)
        online_banks = [
            ("BoG[online]", "mBank"),
            ("TBC[online]", "TBC mobile"),
            ("Credo[online]", "MyCredo"),
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
                    row = self._make_row(bank_name, rates)
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

    async def get_best_rates_for_pair(
        self, sell_currency: str, get_currency: str
    ) -> list[BestRateResult]:
        """
        Get the best rates for a given currency pair, following business rules:
        - Always include NBG, mBank, TBC mobile, MyCredo.
        - For each, calculate the rate for the selected pair (using GEL as intermediary if needed).
        - For the top 5, exclude NBG and all orgs of type "Online", and only include orgs with both rates needed.
        - Sort by the best first-step rate for the user.

        Args:
            sell_currency: The currency the user wants to sell.
            get_currency: The currency the user wants to get.

        Returns:
            List of dicts with organization name and calculated rate.
        """

        # Helper to calculate effective rate for a pair via GEL
        def calculate_pair_rate(
            rates: dict[str, Any], sell: str, get: str
        ) -> float | None:
            # If direct GEL pair
            if sell == "GEL":
                # User sells GEL, wants to buy get_currency: use sell_rate for get_currency
                rate = rates.get(get)
                return 1 / rate["sell_rate"] if rate and rate["sell_rate"] else None
            elif get == "GEL":
                # User sells sell_currency, wants GEL: use buy_rate for sell_currency
                rate = rates.get(sell)
                return rate["buy_rate"] if rate and rate["buy_rate"] else None
            else:
                # Cross: sell -> GEL -> get
                rate_sell = rates.get(sell)
                rate_get = rates.get(get)
                if (
                    rate_sell
                    and rate_sell["buy_rate"]
                    and rate_get
                    and rate_get["sell_rate"]
                ):
                    gel_amount = rate_sell["buy_rate"]  # sell_currency -> GEL
                    return gel_amount / rate_get["sell_rate"]  # GEL -> get_currency
                return None

        # 1. Always include NBG, mBank, TBC mobile, MyCredo
        always_include = [
            ("National Bank of Georgia", "NBG"),
            ("mBank", None),
            ("TBC mobile", None),
            ("MyCredo", None),
        ]
        results: list[BestRateResult] = []
        shown_org_ids = set()
        for org_name, ext_ref in always_include:
            org = None
            if ext_ref:
                org = await self.organization_repo.find_one_by(external_ref_id=ext_ref)
            else:
                org = await self.organization_repo.find_one_by(name=org_name)
            if not org or not org.is_active:
                continue
            shown_org_ids.add(org.id)
            offices = await self.office_repo.get_by_organization(org.id)
            if not offices:
                continue
            office = offices[0]
            rates = await self.rate_repo.get_rates_by_office(office.id, limit=10)
            # Build a dict: currency -> {buy_rate, sell_rate}
            rate_map = {}
            for r in rates:
                rate_map[r.currency] = {
                    "buy_rate": r.buy_rate,
                    "sell_rate": r.sell_rate,
                }
            eff_rate = calculate_pair_rate(rate_map, sell_currency, get_currency)
            if eff_rate is not None:
                results.append(
                    {
                        "organization": org_name,
                        "rate": eff_rate,
                    }
                )

        # 2. Top 5 from other orgs (exclude NBG, Online)
        all_orgs = await self.organization_repo.get_active_organizations()
        candidates: list[BestRateResult] = []
        for org in all_orgs:
            if org.id in shown_org_ids:
                continue
            if getattr(org, "type", None) == "Online":
                continue
            offices = await self.office_repo.get_by_organization(org.id)
            if not offices:
                continue
            office = offices[0]
            rates = await self.rate_repo.get_rates_by_office(office.id, limit=10)
            rate_map = {}
            for r in rates:
                rate_map[r.currency] = {
                    "buy_rate": r.buy_rate,
                    "sell_rate": r.sell_rate,
                }
            eff_rate = calculate_pair_rate(rate_map, sell_currency, get_currency)
            if eff_rate is not None:
                candidates.append(
                    {
                        "organization": org.name,
                        "rate": eff_rate,
                    }
                )
        # Only keep candidates with a float rate
        candidates = [c for c in candidates if isinstance(c["rate"], float)]
        candidates.sort(key=lambda x: x["rate"], reverse=True)
        results.extend(candidates[:5])
        return results
