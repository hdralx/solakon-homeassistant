"""Config flow for Solakon integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolakonAuthError, SolakonApiError, request_otp, verify_otp
from .const import ANON_KEY, CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_REFRESH_TOKEN, DB_BASE, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_EMAIL_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
STEP_OTP_SCHEMA = vol.Schema({vol.Required("otp"): str})


class SolakonConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email = user_input[CONF_EMAIL].strip().lower()
            session = async_get_clientsession(self.hass)
            try:
                await request_otp(session, self._email)
                return await self.async_step_otp()
            except SolakonApiError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error requesting OTP")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_EMAIL_SCHEMA,
            errors=errors,
        )

    async def async_step_otp(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            otp = user_input["otp"].strip()
            session = async_get_clientsession(self.hass)
            try:
                tokens = await verify_otp(session, self._email, otp)
                await self.async_set_unique_id(self._email)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Solakon ({self._email})",
                    data={
                        CONF_EMAIL: self._email,
                        CONF_ACCESS_TOKEN: tokens["access_token"],
                        CONF_REFRESH_TOKEN: tokens["refresh_token"],
                    },
                )
            except SolakonAuthError:
                errors["base"] = "invalid_auth"
            except SolakonApiError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error verifying OTP")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="otp",
            data_schema=STEP_OTP_SCHEMA,
            errors=errors,
            description_placeholders={"email": self._email},
        )
