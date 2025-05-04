"""
SyncService module for fetching and synchronizing exchange rate data.
"""

import uuid
from typing import List, Dict, Any

from sqlmodel import Session

from src.config.logging_conf import get_logger
from src.external_connectors.myfin.api_connector import MyFinApiConnector
from src.external_connectors.myfin.schemas import ExchangeResponse, MapResponse
from src.utils.http_client import get_http_client
from src.db.session import get_session, get_db_session
from src.db.repositories.organization_repository import OrganizationRepository
from src.db.repositories.office_repository import OfficeRepository
from src.db.repositories.rate_repository import RateRepository
from src.db.repositories.schedule_repository import ScheduleRepository
from src.utils.schedule_parser import parse_schedule
from src.db.models.schedule import Schedule

logger = get_logger(__name__)


class SyncService:
    """
    Service for synchronizing exchange rate data from MyFin API to the database.
    """

    def __init__(
        self,
        db_session: Session,
        api_connector: MyFinApiConnector,
    ):
        """
        Initialize the SyncService.

        Args:
            db_session: The database session. If not provided, a new session will be created.
            api_connector: The MyFin API connector. If not provided, a new connector will be created.
        """
        self.session = db_session
        self.api_connector = api_connector
        self.organization_repo = OrganizationRepository(session=self.session)
        self.office_repo = OfficeRepository(session=self.session)
        self.rate_repo = RateRepository(session=self.session)
        self.schedule_repo = ScheduleRepository(
            session=self.session, model_class=Schedule
        )

    async def fetch_exchange_data(
        self,
        city: str = "tbilisi",
        include_online: bool = True,
        availability: str = "All",
    ) -> ExchangeResponse:
        """
        Fetch exchange rate data from the MyFin API.

        Args:
            city: The city for which to fetch exchange rates. Default is "tbilisi".
            include_online: Whether to include online exchange rates. Default is True.
            availability: The availability filter. Default is "All".

        Returns:
            The exchange rate data as an ExchangeResponse object.
        """
        logger.info(
            f"Fetching exchange data for city: {city}, include_online: {include_online}, availability: {availability}"
        )

        # Create API connector if not provided
        if self.api_connector is None:
            http_client = get_http_client()
            self.api_connector = MyFinApiConnector(
                http_client_session=http_client.session
            )

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
        city: str = "tbilisi",
        include_online: bool = False,
        availability: str = "All",
    ) -> MapResponse:
        """
        Fetch office coordinates data from the MyFin API.

        Args:
            city: The city for which to fetch coordinates. Default is "tbilisi".
            include_online: Whether to include online exchange rates. Default is False.
            availability: The availability filter. Default is "All".

        Returns:
            The office coordinates data as a MapResponse object.
        """
        logger.info(
            f"Fetching map data for city: {city}, include_online: {include_online}, availability: {availability}"
        )

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

    async def _process_map_data(self, map_data: MapResponse) -> dict[str, int]:
        """
        Process office coordinates and schedules from the map data.

        Args:
            map_data: The map data from the MyFin API.

        Returns:
            A dictionary with statistics about the processing.
        """
        stats = {
            "offices_updated": 0,
            "schedules_created": 0,
            "schedules_updated": 0,
        }

        # Process each office
        for office_data in map_data.offices:
            # Find the office by external_ref_id
            existing_office = self.office_repo.find_one_by(
                external_ref_id=str(office_data.id)
            )

            if existing_office:
                # Update office coordinates
                office_dict = {
                    "lat": office_data.latitude,
                    "lng": office_data.longitude,
                }

                # Update existing office
                self.office_repo.update(db_obj=existing_office, obj_in=office_dict)
                stats["offices_updated"] += 1

                # Process schedules
                if office_data.schedule:
                    # Delete existing schedules
                    self.schedule_repo.delete_by_office_id(existing_office.id)

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
                            office_id=existing_office.id,
                        )
                        for schedule in parsed_schedules
                    ]

                    # Create new schedules
                    self.schedule_repo.create_many(schedule_objects)
                    stats["schedules_created"] += len(schedule_objects)

        return stats

    async def sync_data(
        self,
        city: str = "tbilisi",
        include_online: bool = True,
        availability: str = "All",
    ) -> dict[str, int]:
        """
        Synchronize exchange rate data from the MyFin API to the database.

        Args:
            city: The city for which to fetch exchange rates. Default is "tbilisi".
            include_online: Whether to include online exchange rates. Default is True.
            availability: The availability filter. Default is "All".

        Returns:
            A dictionary with statistics about the synchronization.
        """
        logger.info("Starting data synchronization")

        # Create a session if not provided
        session_created = False
        if self.session is None:
            session_gen = get_session()
            self.session = next(session_gen)
            session_created = True

        try:
            # Fetch exchange rate data from the API
            exchange_data = await self.fetch_exchange_data(
                city=city, include_online=include_online, availability=availability
            )

            # Process organizations and offices
            stats = await self._process_organizations_and_offices(exchange_data)

            # Fetch map data from the API
            map_data = await self.fetch_map_data(
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
        finally:
            # Close the session if we created it
            if session_created and self.session is not None:
                self.session.close()

    async def _process_organizations_and_offices(
        self, exchange_data: ExchangeResponse
    ) -> dict[str, int]:
        """
        Process organizations and offices from the exchange data.

        Args:
            exchange_data: The exchange data from the MyFin API.

        Returns:
            A dictionary with statistics about the processing.
        """
        stats = {
            "organizations_created": 0,
            "organizations_updated": 0,
            "offices_created": 0,
            "offices_updated": 0,
            "offices_deactivated": 0,
            "rates_created": 0,
            "rates_updated": 0,
        }

        # Keep track of active organization and office IDs
        active_org_ids: set[uuid.UUID] = set()
        active_office_ids: set[uuid.UUID] = set()

        # Process each organization
        for org_data in exchange_data.organizations:
            # Save organization to database
            org_dict = {
                "external_ref_id": str(org_data.id),
                "name": org_data.name.en,
                "website": org_data.link,
                "logo_url": org_data.icon,
            }

            # Check if organization exists by external_ref_id
            existing_org = self.organization_repo.find_one_by(
                external_ref_id=str(org_data.id)
            )

            if existing_org:
                # Update existing organization
                org = self.organization_repo.update(
                    db_obj=existing_org, obj_in=org_dict
                )
                stats["organizations_updated"] += 1
            else:
                # Create new organization
                org = self.organization_repo.create(obj_in=org_dict)
                stats["organizations_created"] += 1

            # Add to active organization IDs
            active_org_ids.add(org.id)

            # Process each office for this organization
            for office_data in org_data.offices:
                # Save office to database
                office_dict = {
                    "external_ref_id": str(office_data.id),
                    "name": office_data.name.en,
                    "address": office_data.address.en,
                    "lat": 0.0,  # We don't have lat/lng in the API response, so use defaults
                    "lng": 0.0,
                    "organization_id": org.id,
                }

                # Check if office exists by external_ref_id
                existing_office = self.office_repo.find_one_by(
                    external_ref_id=str(office_data.id)
                )

                if existing_office:
                    # Update existing office
                    office = self.office_repo.update(
                        db_obj=existing_office, obj_in=office_dict
                    )
                    stats["offices_updated"] += 1
                else:
                    # Create new office
                    office = self.office_repo.create(obj_in=office_dict)
                    stats["offices_created"] += 1

                # Add to active office IDs
                active_office_ids.add(office.id)

                # Process rates for this office
                for currency, rate_data in office_data.rates.items():
                    # Save rate to database
                    rate_dict = {
                        "office_id": office.id,
                        "currency": currency,
                        "buy_rate": rate_data.buy,
                        "sell_rate": rate_data.sell,
                        "timestamp": rate_data.time,
                    }

                    # Upsert rate
                    rate = self.rate_repo.upsert(rate_dict)
                    if hasattr(rate, "_is_new") and rate._is_new:
                        stats["rates_created"] += 1
                    else:
                        stats["rates_updated"] += 1

        # Mark inactive organizations and offices
        if active_org_ids:
            self.organization_repo.mark_inactive_if_not_in_list(list(active_org_ids))

        if active_office_ids:
            stats["offices_deactivated"] = (
                self.office_repo.mark_inactive_if_not_in_list(list(active_office_ids))
            )

        return stats


async def sync_exchange_data():
    """
    Asynchronous function to fetch exchange rate data from MyFin and save it to the database.

    Returns:
        None
    """
    logger.info("Starting exchange data synchronization")

    try:
        with get_db_session() as db_session:
            http_client = get_http_client()
            myfin_api_connector = MyFinApiConnector(
                http_client_session=http_client.session
            )
            sync_service = SyncService(
                db_session=db_session, api_connector=myfin_api_connector
            )

            # Sync data from the MyFin API to the database
            stats = await sync_service.sync_data()

            logger.info(f"Exchange data synchronization completed: {stats}")

        logger.info(f"Exchange data synchronization completed: {stats}")
    except Exception as e:
        logger.error(f"Error during exchange data synchronization: {e}")
        raise
