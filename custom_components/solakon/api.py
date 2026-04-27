"""Solakon API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import ANON_KEY, API_BASE, DB_BASE

_LOGGER = logging.getLogger(__name__)


class SolakonAuthError(Exception):
    pass


class SolakonApiError(Exception):
    pass


class SolakonClient:
    def __init__(self, session: aiohttp.ClientSession, access_token: str, refresh_token: str) -> None:
        self._session = session
        self._access_token = access_token
        self._refresh_token = refresh_token

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": self._access_token,
            "X-App-Version": "1.0.0",
            "Content-Type": "application/json",
        }

    async def refresh_session(self) -> None:
        url = f"{DB_BASE}/auth/v1/token?grant_type=refresh_token"
        async with self._session.post(
            url,
            headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
            json={"refresh_token": self._refresh_token},
        ) as resp:
            if resp.status != 200:
                raise SolakonAuthError(f"Token refresh failed: {resp.status}")
            data = await resp.json()
            self._access_token = data["access_token"]
            self._refresh_token = data["refresh_token"]

    async def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{API_BASE}{path}"
        async with self._session.get(url, headers=self._auth_headers(), params=params) as resp:
            if resp.status == 401:
                await self.refresh_session()
                async with self._session.get(url, headers=self._auth_headers(), params=params) as retry:
                    if retry.status != 200:
                        raise SolakonApiError(f"GET {path} failed: {retry.status}")
                    return await retry.json()
            if resp.status != 200:
                raise SolakonApiError(f"GET {path} failed: {resp.status}")
            return await resp.json()

    async def get_groups(self) -> list[dict]:
        data = await self._get("/v1/user/groups")
        return data if isinstance(data, list) else data.get("data", [])

    async def get_inverter_aggregated(self, device_id: str) -> dict:
        return await self._get(f"/v1/inverter/{device_id}/aggregated")

    async def get_battery_aggregated(self, device_id: str) -> dict:
        return await self._get(f"/v1/batteries/{device_id}/aggregated")

    async def get_user(self) -> dict:
        return await self._get("/v1/user")


async def verify_token(session: aiohttp.ClientSession, access_token: str) -> dict:
    """Verify an access token and return user info."""
    url = f"{DB_BASE}/auth/v1/user"
    async with session.get(
        url,
        headers={"apikey": ANON_KEY, "Authorization": f"Bearer {access_token}"},
    ) as resp:
        if resp.status == 401:
            raise SolakonAuthError("Invalid or expired token")
        if resp.status != 200:
            raise SolakonApiError(f"Token verification failed: {resp.status}")
        return await resp.json()
