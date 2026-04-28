"""Data coordinator for Solakon integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolakonApiError, SolakonAuthError, SolakonClient
from .const import CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SolakonCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.entry = entry
        session = async_get_clientsession(hass)
        self.client = SolakonClient(
            session,
            entry.data[CONF_ACCESS_TOKEN],
            entry.data[CONF_REFRESH_TOKEN],
        )

    def _persist_tokens(self) -> None:
        """Save current tokens to config entry if they changed."""
        if (
            self.client.access_token != self.entry.data[CONF_ACCESS_TOKEN]
            or self.client.refresh_token != self.entry.data[CONF_REFRESH_TOKEN]
        ):
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    CONF_ACCESS_TOKEN: self.client.access_token,
                    CONF_REFRESH_TOKEN: self.client.refresh_token,
                },
            )
            _LOGGER.debug("Solakon tokens persisted to config entry")

    async def _async_update_data(self) -> dict:
        try:
            # Sequential calls so the refresh lock works correctly —
            # parallel calls would race to consume the single-use refresh token
            groups = await self.client.get_groups()
            self._persist_tokens()

            result: dict = {"groups": [], "inverters": {}, "batteries": {}}

            for group in groups:
                result["groups"].append(group)

                inverter = group.get("inverter")
                if inverter and inverter.get("deviceId"):
                    device_id = inverter["deviceId"]
                    try:
                        data = await self.client.get_inverter_aggregated(device_id)
                        result["inverters"][device_id] = data
                        self._persist_tokens()
                    except SolakonApiError as err:
                        _LOGGER.warning("Could not fetch inverter %s: %s", device_id, err)

                for battery in group.get("batteries", []):
                    if battery.get("deviceId"):
                        device_id = battery["deviceId"]
                        try:
                            data = await self.client.get_battery_aggregated(device_id)
                            result["batteries"][device_id] = data
                            self._persist_tokens()
                        except SolakonApiError as err:
                            _LOGGER.warning("Could not fetch battery %s: %s", device_id, err)

            return result

        except SolakonAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except SolakonApiError as err:
            raise UpdateFailed(f"API error: {err}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error: {err}") from err
