"""The Kerbl Welt integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import KerblweltDataUpdateCoordinator

# Import API client
import sys
sys.path.insert(0, "/Users/sgarrity/projects/kerblwelt/kerblwelt-api")
from kerblwelt_api import KerblweltClient, ConnectionError as KerblweltConnectionError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kerbl Welt from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    client = KerblweltClient()
    await client.__aenter__()

    try:
        # Authenticate
        await client.authenticate(
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
    except KerblweltConnectionError as err:
        _LOGGER.error("Failed to connect to Kerbl Welt API: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"Cannot connect to Kerbl Welt API: {err}") from err
    except Exception as err:
        _LOGGER.exception("Failed to authenticate: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"Authentication failed: {err}") from err

    # Create coordinator
    coordinator = KerblweltDataUpdateCoordinator(hass, client, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and client
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Close client
        data = hass.data[DOMAIN].pop(entry.entry_id)
        client = data["client"]
        await client.close()

    return unload_ok
