"""Config flow for Kerbl Welt integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Import the API client inline to avoid dependencies during manifest loading
# We'll use the actual kerblwelt-api library in production, but for now
# we'll create a simple inline client for testing


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Import here to avoid dependency issues
    import sys
    sys.path.insert(0, "/Users/sgarrity/projects/kerblwelt/kerblwelt-api")
    from kerblwelt_api import KerblweltClient, InvalidCredentialsError

    try:
        async with KerblweltClient() as client:
            await client.authenticate(data[CONF_EMAIL], data[CONF_PASSWORD])
            user = await client.get_user()

            # Return info that you want to store in the config entry
            return {
                "title": f"Kerbl Welt ({data[CONF_EMAIL]})",
                "user_id": user.id,
            }

    except InvalidCredentialsError as err:
        _LOGGER.error("Invalid credentials: %s", err)
        raise InvalidAuth from err
    except aiohttp.ClientError as err:
        _LOGGER.error("Cannot connect: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise UnknownError from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kerbl Welt."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except UnknownError:
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(info["user_id"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownError(HomeAssistantError):
    """Error to indicate an unknown error occurred."""
