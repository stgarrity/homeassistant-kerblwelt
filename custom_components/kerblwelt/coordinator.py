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
from kerblwelt_api import (
    KerblweltClient,
    AuthenticationError,
    InvalidCredentialsError,
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

        except (AuthenticationError, APIError) as err:
            # The access token expired or the token-refresh flow failed. Because
            # the coordinator holds the account credentials, recover by performing
            # a full re-login and retrying once - rather than going dark until the
            # next Home Assistant restart. Non-auth API errors (e.g. 429 rate
            # limiting) are left to the coordinator's normal retry backoff.
            if isinstance(err, APIError) and err.status_code not in (401, None):
                _LOGGER.error("API error: %s", err)
                raise UpdateFailed(
                    f"Error communicating with Kerbl Welt API: {err}"
                ) from err

            _LOGGER.warning(
                "Auth/token failure (%s); re-authenticating with stored credentials",
                err,
            )
            try:
                await self.client.authenticate(
                    self.entry.data[CONF_EMAIL],
                    self.entry.data[CONF_PASSWORD],
                )
            except InvalidCredentialsError as auth_err:
                # Credentials are genuinely bad - prompt the user to re-auth.
                _LOGGER.error("Stored credentials rejected: %s", auth_err)
                raise ConfigEntryAuthFailed("Authentication failed") from auth_err
            except Exception as auth_err:  # noqa: BLE001
                # Transient failure during re-login - retry on the next interval.
                raise UpdateFailed(
                    f"Re-authentication failed: {auth_err}"
                ) from auth_err

            try:
                return await self.client.get_all_device_data()
            except Exception as err2:  # noqa: BLE001
                raise UpdateFailed(
                    f"Error fetching data after re-authentication: {err2}"
                ) from err2

        except KerblweltConnectionError as err:
            # Connection error - will retry automatically
            _LOGGER.error("Connection error: %s", err)
            raise UpdateFailed(f"Error connecting to Kerbl Welt API: {err}") from err

        except Exception as err:
            # Unexpected error
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
