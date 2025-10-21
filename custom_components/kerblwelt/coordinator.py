"""DataUpdateCoordinator for Kerbl Welt integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL, DOMAIN

# Import API client
import sys
sys.path.insert(0, "/Users/sgarrity/projects/kerblwelt/kerblwelt-api")
from kerblwelt_api import (
    KerblweltClient,
    InvalidCredentialsError,
    TokenExpiredError,
    APIError,
    ConnectionError as KerblweltConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class KerblweltDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Kerbl Welt data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: KerblweltClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint.

        This is the only place we should be calling the API.
        """
        try:
            # Get all device data in one efficient call
            device_data = await self.client.get_all_device_data()

            _LOGGER.debug(
                "Successfully fetched data for %d device(s)",
                len(device_data),
            )

            return device_data

        except (InvalidCredentialsError, TokenExpiredError) as err:
            # Auth error - raise ConfigEntryAuthFailed to trigger re-authentication
            _LOGGER.error("Authentication error: %s", err)
            raise ConfigEntryAuthFailed("Authentication failed") from err

        except KerblweltConnectionError as err:
            # Connection error - will retry automatically
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Error connecting to Kerbl Welt API: {err}") from err

        except APIError as err:
            # API error - will retry automatically
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"Error communicating with Kerbl Welt API: {err}") from err

        except Exception as err:
            # Unexpected error
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
