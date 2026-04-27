"""Config flow for Solakon integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolakonAuthError, SolakonApiError, verify_token
from .const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_REFRESH_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_TOKEN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Required(CONF_REFRESH_TOKEN): str,
    }
)


class SolakonConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                user = await verify_token(session, user_input[CONF_ACCESS_TOKEN])
                email = user.get("email", "solakon")
                await self.async_set_unique_id(email)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Solakon ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                        CONF_REFRESH_TOKEN: user_input[CONF_REFRESH_TOKEN],
                    },
                )
            except SolakonAuthError:
                errors["base"] = "invalid_auth"
            except SolakonApiError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_TOKEN_SCHEMA,
            errors=errors,
            description_placeholders={
                "instructions": (
                    "1. Öffne app.solakon.de und logge dich ein\n"
                    "2. Drücke F12 → Application → Local Storage\n"
                    "3. Suche nach 'sb-banzku...-auth-token'\n"
                    "4. Kopiere 'access_token' und 'refresh_token'"
                )
            },
        )
