"""
SyncService module for fetching and synchronizing exchange rate data.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Organization
from src.db.session import async_get_db_session
from src.config.logging_conf import get_logger
from src.external_connectors.myfin.api_connector import MyFinApiConnector
from src.external_connectors.myfin.schemas import (
    ExchangeResponse,
    MapResponse,
    Office as OfficeData,
    Organization as OrganizationData,
)
from src.utils.http_client import get_http_client
from src.repositories.organization_repository import AsyncOrganizationRepository
from src.repositories.office_repository import AsyncOfficeRepository
from src.repositories.rate_repository import AsyncRateRepository
from src.repositories.schedule_repository import AsyncScheduleRepository
from src.utils.schedule_parser import parse_schedule
from src.db.models.schedule import Schedule
from src.db.models.office import Office
from src.db.models.rate import Rate

logger = get_logger(__name__)

# Constants
NBG_ORG_REF = "NBG"
NBG_ORG_NAME = "National Bank of Georgia"
NBG_OFFICE_REF = "NBG_OFFICE"
NBG_OFFICE_NAME = "NBG Main Office"
NBG_OFFICE_ADDRESS = "3, Gudamakari St, Tbilisi"
VIRTUAL_OFFICE_NAME = "Online Office"
VIRTUAL_OFFICE_ADDRESS = "Online"
DEFAULT_CITY = "tbilisi"
DEFAULT_AVAILABILITY = "All"


@dataclass
class SyncStats:
    """Statistics about the synchronization process."""

    organizations_created: int = 0
    organizations_updated: int = 0
    offices_created: int = 0
    offices_updated: int = 0
    offices_deactivated: int = 0
    rates_created: int = 0
    rates_updated: int = 0
    schedules_created: int = 0
    schedules_updated: int = 0

    def update(self, other: Dict[str, int]) -> None:
        """Update stats from a dictionary."""
        for key, value in other.items():
            if hasattr(self, key):
                setattr(self, key, getattr(self, key) + value)

    def to_dict(self) -> Dict[str, int]:
        """Convert stats to a dictionary."""
        return {k: v for k, v in self.__dict__.items()}


class DataFetcher:
    """
    Service for fetching data from the MyFin API.
    """

    def __init__(self, api_connector: Optional[MyFinApiConnector] = None):
        """
        Initialize the DataFetcher.

        Args:
            api_connector: The MyFin API connector. If not provided, a new connector will be created.
        """
        self.api_connector = api_connector

    async def ensure_api_connector(self) -> None:
        """Ensure that the API connector is initialized."""
        if self.api_connector is None:
            http_client = get_http_client()
            self.api_connector = MyFinApiConnector(
                http_client_session=http_client.session
            )

    async def fetch_exchange_data(
        self,
        city: str = DEFAULT_CITY,
        include_online: bool = True,
        availability: str = DEFAULT_AVAILABILITY,
    ) -> ExchangeResponse:
        """
        Fetch exchange rate data from the MyFin API.

        Args:
            city: The city for which to fetch exchange rates.
            include_online: Whether to include online exchange rates.
            availability: The availability filter.

        Returns:
            The exchange rate data as an ExchangeResponse object.
        """
        logger.info(
            f"Fetching exchange data for city: {city}, include_online: {include_online}, availability: {availability}"
        )

        await self.ensure_api_connector()

        if self.api_connector is None:
            raise RuntimeError("API connector is not initialized.")

        try:
            # Fetch data from the API
            response_data = await self.api_connector.get_exchange_rates(
                city=city, include_online=include_online, availability=availability
            )

            # Parse the response using the ExchangeResponse schema
            exchange_response = ExchangeResponse.model_validate(response_data)
            logger.info(
                f"Successfully fetched exchange data: {len(exchange_response.organizations)} organizations"
            )
            return exchange_response
        except Exception as e:
            logger.error(f"Error fetching exchange data: {e}")
            raise

    async def fetch_map_data(
        self,
        city: str = DEFAULT_CITY,
        include_online: bool = False,
        availability: str = DEFAULT_AVAILABILITY,
    ) -> MapResponse:
        """
        Fetch office coordinates data from the MyFin API.

        Args:
            city: The city for which to fetch coordinates.
            include_online: Whether to include online exchange rates.
            availability: The availability filter.

        Returns:
            The office coordinates data as a MapResponse object.
        """
        logger.info(
            f"Fetching map data for city: {city}, include_online: {include_online}, availability: {availability}"
        )

        await self.ensure_api_connector()

        if self.api_connector is None:
            raise RuntimeError("API connector is not initialized.")

        try:
            # Fetch data from the API
            response_data = await self.api_connector.get_office_coordinates(
                city=city, include_online=include_online, availability=availability
            )

            # Parse the response using the MapResponse schema
            map_response = MapResponse.model_validate(response_data)
            logger.info(
                f"Successfully fetched map data: {len(map_response.offices)} offices"
            )
            return map_response
        except Exception as e:
            logger.error(f"Error fetching map data: {e}")
            raise


class SyncService:
    """
    Service for synchronizing exchange rate data from MyFin API to the database.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        api_connector: Optional[MyFinApiConnector] = None,
    ):
        """
        Initialize the SyncService.

        Args:
            db_session: The async database session.
            api_connector: The MyFin API connector. If not provided, a new connector will be created.
        """
        logger.info(f"[SyncService] Initialized with db_session: {db_session}")
        self.session = db_session
        if api_connector is not None:
            self.data_fetcher = DataFetcher(api_connector)
        else:
            self.data_fetcher = DataFetcher()
        self.organization_repo = AsyncOrganizationRepository(session=self.session)
        self.office_repo = AsyncOfficeRepository(session=self.session)
        self.rate_repo = AsyncRateRepository(session=self.session, model_class=Rate)
        self.schedule_repo = AsyncScheduleRepository(
            session=self.session, model_class=Schedule
        )

        # Log the database connection details
        try:
            bind = db_session.get_bind()
            engine = getattr(bind, "engine", bind)
            url = str(getattr(engine, "url", "unknown"))
            logger.info(f"[SyncService] SQLAlchemy engine URL: {url}")
            if url.startswith("sqlite:///"):
                db_path = url.replace("sqlite:///", "")
                logger.info(f"[SyncService] Using SQLite DB file: {db_path}")
        except Exception as exc:
            logger.warning(f"[SyncService] Could not determine DB file: {exc}")

    async def _create_virtual_office_data(
        self, organization_id: uuid.UUID, external_ref_id: str
    ) -> Optional[OfficeData]:
        """
        Create a virtual office for online banks if it doesn't exist.

        Args:
            organization_id: The ID of the organization.
            external_ref_id: The external reference ID of the organization.

        Returns:
            A virtual office data object if created or found, None otherwise.
        """
        # Check if a virtual office already exists
        existing_virtual_office = await self.office_repo.find_one_by(
            organization_id=organization_id, name=VIRTUAL_OFFICE_NAME
        )

        if existing_virtual_office:
            # Create a simple dictionary to represent the office data
            return OfficeData.model_validate(
                {
                    "id": existing_virtual_office.external_ref_id,
                    "name": {"en": existing_virtual_office.name},
                    "address": {"en": existing_virtual_office.address},
                    "rates": {},
                }
            )
        else:
            # Create a new virtual office
            virtual_office = await self.office_repo.create(
                obj_in={
                    "external_ref_id": f"{external_ref_id}",
                    "name": VIRTUAL_OFFICE_NAME,
                    "address": VIRTUAL_OFFICE_ADDRESS,
                    "lat": 0.0,
                    "lng": 0.0,
                    "organization_id": organization_id,
                    "is_active": True,
                }
            )

            # Create a simple dictionary to represent the office data
            return OfficeData.model_validate(
                {
                    "id": virtual_office.external_ref_id,
                    "name": {"en": virtual_office.name},
                    "address": {"en": virtual_office.address},
                    "rates": {},
                }
            )

    async def _process_map_data(self, map_data: MapResponse) -> Dict[str, int]:
        """
        Process office coordinates and schedules from the map data.

        Args:
            map_data: The map data from the MyFin API.

        Returns:
            A dictionary with statistics about the processing.
        """
        stats = SyncStats()

        # Process each office
        for office_data in map_data.offices:
            try:
                # Find the office by external_ref_id
                existing_office = await self.office_repo.find_one_by(
                    external_ref_id=str(office_data.id)
                )

                if existing_office:
                    # Update office coordinates
                    office_dict = {
                        "lat": office_data.latitude,
                        "lng": office_data.longitude,
                    }

                    # Update existing office
                    await self.office_repo.update(
                        db_obj=existing_office, obj_in=office_dict
                    )
                    stats.offices_updated += 1

                    # Process schedules if available
                    await self._process_office_schedules(
                        existing_office, office_data, stats
                    )
            except Exception as e:
                logger.error(
                    f"Error processing map data for office {office_data.id}: {e}"
                )
                # Continue processing other offices even if one fails

        return stats.to_dict()

    async def _process_office_schedules(
        self, office: Office, office_data: Any, stats: SyncStats
    ) -> None:
        """
        Process schedules for an office.

        Args:
            office: The office to process schedules for.
            office_data: The office data from the API.
            stats: The statistics object to update.
        """
        if not hasattr(office_data, "schedule") or not office_data.schedule:
            return

        try:
            # Delete existing schedules
            await self.schedule_repo.delete_by_office_id(office.id)

            # Convert schedule entries to dictionaries
            schedule_dicts: List[Dict[str, Any]] = [
                {
                    "start": entry.start.model_dump(),
                    "end": entry.end.model_dump() if entry.end else None,
                    "intervals": entry.intervals,
                }
                for entry in office_data.schedule
            ]

            # Parse and create new schedules
            parsed_schedules = parse_schedule(schedule_dicts)
            schedule_objects = [
                Schedule(
                    day=schedule["day"],
                    opens_at=schedule["opens_at"],
                    closes_at=schedule["closes_at"],
                    office_id=office.id,
                )
                for schedule in parsed_schedules
            ]

            # Create new schedules
            await self.schedule_repo.create_many(schedule_objects)
            stats.schedules_created += len(schedule_objects)
        except Exception as e:
            logger.error(f"Error processing schedules for office {office.id}: {e}")
            # Continue processing even if schedule processing fails

    async def sync_data(
        self,
        city: str = DEFAULT_CITY,
        include_online: bool = True,
        availability: str = DEFAULT_AVAILABILITY,
    ) -> Dict[str, int]:
        """
        Synchronize exchange rate data from the MyFin API to the database.

        Args:
            city: The city for which to fetch exchange rates.
            include_online: Whether to include online exchange rates.
            availability: The availability filter.

        Returns:
            A dictionary with statistics about the synchronization.
        """
        logger.info("Starting data synchronization")

        try:
            # Fetch exchange rate data from the API
            exchange_data = await self.data_fetcher.fetch_exchange_data(
                city=city, include_online=include_online, availability=availability
            )

            # Process organizations and offices
            stats = await self._process_organizations_and_offices(exchange_data)

            # Fetch map data from the API
            map_data = await self.data_fetcher.fetch_map_data(
                city=city, include_online=include_online, availability=availability
            )

            # Process map data to update office coordinates
            map_stats = await self._process_map_data(map_data)

            # Combine stats
            stats.update(map_stats)

            logger.info(f"Data synchronization completed: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error during data synchronization: {e}")
            raise

    async def _upsert_nbg_organization_and_rates(
        self, best_rates: Dict[str, Any], stats: SyncStats, timestamp: Optional[datetime] = None
    ) -> Organization:
        """
        Upsert NBG organization, office, and rates from the best field of the API response.

        Args:
            best_rates: The 'best' field from the API response.
            stats: The statistics object to update.
            timestamp: The timestamp to use for the rates (default: now).

        Returns:
            The NBG organization.

        Raises:
            Exception: If there's an error upserting the NBG organization or rates.
        """
        now = timestamp or datetime.now(tz=UTC)

        try:
            # Find or create NBG organization
            org = await self.organization_repo.find_one_by(external_ref_id=NBG_ORG_REF)
            if not org:
                logger.info(f"Creating NBG organization: {NBG_ORG_NAME}")
                org = await self.organization_repo.create(
                    obj_in={
                        "external_ref_id": NBG_ORG_REF,
                        "name": NBG_ORG_NAME,
                        "website": None,
                        "logo_url": None,
                        "is_active": True,
                    }
                )
                stats.organizations_created += 1

            # Find or create NBG office
            office = await self.office_repo.find_one_by(external_ref_id=NBG_OFFICE_REF)
            if not office:
                logger.info(f"Creating NBG office: {NBG_OFFICE_NAME}")
                office = await self.office_repo.create(
                    obj_in={
                        "external_ref_id": NBG_OFFICE_REF,
                        "name": NBG_OFFICE_NAME,
                        "address": NBG_OFFICE_ADDRESS,
                        "lat": 0.0,
                        "lng": 0.0,
                        "organization_id": org.id,
                        "is_active": True,
                    }
                )
                stats.offices_created += 1

            # Upsert rates for each currency
            rate_count = 0
            for currency, rate_data in best_rates.items():
                nbg_value = getattr(rate_data, "nbg", None)
                if nbg_value is not None:
                    rate_dict = {
                        "office_id": office.id,
                        "currency": currency,
                        "buy_rate": nbg_value,
                        "sell_rate": nbg_value,
                        "timestamp": now,
                    }
                    await self.rate_repo.upsert(rate_dict)
                    rate_count += 1

            logger.info(f"Upserted {rate_count} NBG rates")
            return org
        except Exception as e:
            logger.error(f"Error upserting NBG organization and rates: {e}")
            raise

    async def _process_rate(
        self,
        office_id: uuid.UUID,
        currency: str,
        buy_rate: float,
        sell_rate: float,
        timestamp: datetime,
        stats: SyncStats,
    ) -> None:
        """
        Process a rate for an office.

        Args:
            office_id: The ID of the office.
            currency: The currency code.
            buy_rate: The buy rate.
            sell_rate: The sell rate.
            timestamp: The timestamp of the rate.
            stats: The statistics object to update.
        """
        try:
            rate_dict = {
                "office_id": office_id,
                "currency": currency,
                "buy_rate": buy_rate,
                "sell_rate": sell_rate,
                "timestamp": timestamp,
            }

            rate = await self.rate_repo.upsert(rate_dict)

            # Update stats based on whether the rate was created or updated
            if hasattr(rate, "_is_new") and rate._is_new:
                stats.rates_created += 1
            else:
                stats.rates_updated += 1
        except Exception as e:
            logger.error(
                f"Error processing rate for office {office_id}, currency {currency}: {e}"
            )
            # Continue processing other rates even if one fails

    async def _process_organization_offices(
        self,
        org: Organization,
        org_data: OrganizationData,
        active_office_ids: set[uuid.UUID],
        stats: SyncStats,
    ) -> None:
        """
        Process offices for an organization.

        Args:
            org: The organization to process offices for.
            org_data: The organization data from the API.
            active_office_ids: Set of active office IDs to update.
            stats: The statistics object to update.
        """
        # Get offices to process
        offices_to_process = list(org_data.offices)

        # Handle virtual office for online banks
        if org.type == "Online" and not offices_to_process:
            virtual_office_data = await self._create_virtual_office_data(
                organization_id=org.id, external_ref_id=str(org.external_ref_id)
            )
            if virtual_office_data:
                offices_to_process.append(virtual_office_data)
                stats.offices_created += 1

        # Process each office
        for office_data in offices_to_process:
            try:
                # Prepare office data
                office_dict = {
                    "external_ref_id": str(office_data.id),
                    "name": office_data.name.en,
                    "address": office_data.address.en,
                    "lat": 0.0,  # Will be updated from map data later
                    "lng": 0.0,
                    "organization_id": org.id,
                }

                # Find or create office
                existing_office = await self.office_repo.find_one_by(
                    external_ref_id=str(office_data.id)
                )

                if existing_office:
                    # Update existing office
                    office = await self.office_repo.update(
                        db_obj=existing_office, obj_in=office_dict
                    )
                    stats.offices_updated += 1
                else:
                    # Create new office
                    office = await self.office_repo.create(obj_in=office_dict)
                    stats.offices_created += 1

                # Add to active office IDs
                active_office_ids.add(office.id)

                # Process rates for online banks
                if (
                    org.type == "Online"
                    and not office_data.rates
                    and hasattr(org_data, "best")
                    and org_data.best
                ):
                    now = datetime.now(tz=UTC)
                    for currency, org_rate in org_data.best.items():
                        await self._process_rate(
                            office_id=office.id,
                            currency=currency,
                            buy_rate=org_rate.buy,
                            sell_rate=org_rate.sell,
                            timestamp=now,
                            stats=stats,
                        )

                # Process regular rates
                for currency, rate_data in office_data.rates.items():
                    await self._process_rate(
                        office_id=office.id,
                        currency=currency,
                        buy_rate=rate_data.buy,
                        sell_rate=rate_data.sell,
                        timestamp=rate_data.time,
                        stats=stats,
                    )
            except Exception as e:
                logger.error(f"Error processing office {office_data.id}: {e}")
                # Continue processing other offices even if one fails

    async def _process_organizations_and_offices(
        self, exchange_data: ExchangeResponse
    ) -> Dict[str, int]:
        """
        Process organizations and offices from the exchange data.

        Args:
            exchange_data: The exchange data from the MyFin API.

        Returns:
            A dictionary with statistics about the processing.
        """
        stats = SyncStats()

        # Keep track of active organization and office IDs
        active_org_ids: set[uuid.UUID] = set()
        active_office_ids: set[uuid.UUID] = set()

        try:
            # Upsert NBG organization, office, and rates
            nbg_org = await self._upsert_nbg_organization_and_rates(
                best_rates=exchange_data.best,
                stats=stats,
            )
            active_org_ids.add(nbg_org.id)

            # Process each organization
            for org_data in exchange_data.organizations:
                try:
                    # Prepare organization data
                    org_dict = {
                        "external_ref_id": str(org_data.id),
                        "name": org_data.name.en,
                        "website": org_data.link,
                        "logo_url": org_data.icon,
                        "type": org_data.type,
                    }

                    # Find or create organization
                    existing_org = await self.organization_repo.find_one_by(
                        external_ref_id=str(org_data.id)
                    )

                    if existing_org:
                        # Update existing organization
                        org = await self.organization_repo.update(
                            db_obj=existing_org, obj_in=org_dict
                        )
                        stats.organizations_updated += 1
                    else:
                        # Create new organization
                        org = await self.organization_repo.create(obj_in=org_dict)
                        stats.organizations_created += 1

                    # Add to active organization IDs
                    active_org_ids.add(org.id)

                    # Process offices for this organization
                    await self._process_organization_offices(
                        org=org,
                        org_data=org_data,
                        active_office_ids=active_office_ids,
                        stats=stats,
                    )
                except Exception as e:
                    logger.error(f"Error processing organization {org_data.id}: {e}")
                    # Continue processing other organizations even if one fails

            # Mark inactive organizations and offices
            if active_org_ids:
                await self.organization_repo.mark_inactive_if_not_in_list(
                    list(active_org_ids)
                )

            if active_office_ids:
                stats.offices_deactivated = (
                    await self.office_repo.mark_inactive_if_not_in_list(
                        list(active_office_ids)
                    )
                )

            return stats.to_dict()
        except Exception as e:
            logger.error(f"Error processing organizations and offices: {e}")
            raise


async def sync_exchange_data(
    city: str = DEFAULT_CITY,
    include_online: bool = True,
    availability: str = DEFAULT_AVAILABILITY,
) -> Dict[str, int]:
    """
    Asynchronous function to fetch exchange rate data from MyFin and save it to the database.

    Args:
        city: The city for which to fetch exchange rates.
        include_online: Whether to include online exchange rates.
        availability: The availability filter.

    Returns:
        A dictionary with statistics about the synchronization.

    Raises:
        Exception: If there's an error during the synchronization process.
    """
    logger.info("Starting exchange data synchronization")

    try:
        # Create HTTP client and API connector
        http_client = get_http_client()
        myfin_api_connector = MyFinApiConnector(http_client_session=http_client.session)

        # Create database session
        async with async_get_db_session() as db_session:
            # Create sync service
            sync_service = SyncService(
                db_session=db_session, api_connector=myfin_api_connector
            )

            # Sync data
            stats = await sync_service.sync_data(
                city=city, include_online=include_online, availability=availability
            )

            logger.info(f"Exchange data synchronization completed: {stats}")
            return stats
    except Exception as e:
        logger.error(f"Error during exchange data synchronization: {e}")
        raise
