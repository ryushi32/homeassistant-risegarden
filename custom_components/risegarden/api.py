import logging
import time
from typing import Any, Dict, Optional

import aiohttp

_LOGGER = logging.getLogger(__name__)


class RiseGardenAPIError(Exception):
    """Generic exception for the Rise Garden API client."""


class RiseGardenClient:
    """Async client for the Rise Garden cloud API

    Implements login/refresh and request wrapper for endpoints under the
    prod-api.risegds.com/v2 base URL.
    """

    def __init__(self, session: aiohttp.ClientSession, email: str, password: str):
        self._session = session
        self._email = email
        self._password = password
        self._base = "https://prod-api.risegds.com/v2"

        # token info
        self._access_token: str = ""
        self._refresh_token: str = ""
        self._user_id: str = ""
        # expires_at is stored as epoch ms (matches the upstream logic)
        self._expires_at: int = 0

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _token_is_expired(self) -> bool:
        # expire 60s earlier as buffer
        return self._expires_at and (self._expires_at - 60000 < self._now_ms())

    async def login(self) -> bool:
        """Authenticate and populate token fields."""
        url = f"{self._base}/auth/login"
        payload = {"email": self._email, "password": self._password}
        headers = {"Content-Type": "application/json"}
        try:
            async with self._session.post(url, json=payload, headers=headers, timeout=30) as resp:
                data = await resp.json()
                if resp.status != 200:
                    _LOGGER.error("Login failed: %s %s", resp.status, data)
                    return False

                token = data.get("token")
                refresh_token = data.get("refresh_token") or data.get("refreshToken")
                expires_in = data.get("expires_in") or data.get("expiresIn") or 0
                user_id = None
                # some responses return nested user
                if isinstance(data.get("user"), dict):
                    user_id = data["user"].get("id")
                if not token:
                    _LOGGER.error("Login succeeded but no token in response: %s", data)
                    return False

                self._access_token = token
                self._refresh_token = refresh_token or self._refresh_token
                self._user_id = user_id or self._user_id
                self._expires_at = int(expires_in) + self._now_ms()
                return True
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to login: %s", err)
            return False

    async def refresh(self) -> bool:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            return False
        url = f"{self._base}/auth/refresh_token"
        payload = {"refresh_token": self._refresh_token}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }
        try:
            async with self._session.post(url, json=payload, headers=headers, timeout=30) as resp:
                data = await resp.json()
                if resp.status != 200:
                    return False
                token = data.get("token")
                expires_in = data.get("expires_in") or 0
                if not token:
                    return False
                cached_user_id = self._user_id
                self._access_token = token
                # keep same refresh token
                self._user_id = cached_user_id
                self._expires_at = int(expires_in) + self._now_ms()
                return True
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Failed to refresh token: %s", err)
            return False

    async def _refresh_or_login(self) -> bool:
        # If we have a refresh token and token is expired, try refresh.
        if self._refresh_token and self._token_is_expired():
            return await self.refresh()
        # If we don't have an access token, login.
        if not self._access_token:
            return await self.login()
        return True

    async def _request(self, method: str, path: str, params: Optional[Dict] = None, json_body: Optional[Dict] = None) -> Any:
        # Ensure authenticated for non-auth paths
        if path not in ("/auth/login", "/auth/refresh_token"):
            await self._refresh_or_login()

        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        url = f"{self._base}{path}"
        try:
            async with self._session.request(method.upper(), url, headers=headers, params=params, json=json_body, timeout=30) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise RiseGardenAPIError(f"API request failed for {path}: {resp.status} {data}")
                return data
        except aiohttp.ClientError as err:
            _LOGGER.error("API request failed for %s: %s", path, err)
            raise RiseGardenAPIError(str(err))

    # High level methods mapped from the homebridge client
    async def get_gardens(self) -> Any:
        return await self._request("GET", "/gardens")

    async def get_device_status(self, garden_id: int) -> Any:
        return await self._request("GET", f"/gardens/{garden_id}/device/status")

    async def get_current_temperature(self, garden_id: int) -> Optional[float]:
        status = await self.get_device_status(garden_id)
        # upstream returns at (air temp?) under data.at
        return status.get("data", {}).get("at")

    async def get_light_level(self, garden_id: int) -> Optional[int]:
        status = await self.get_device_status(garden_id)
        return status.get("data", {}).get("lamp_level")

    async def set_light_level(self, garden_id: int, level: int) -> Any:
        body = {"light_level": level, "wait_for_response": True}
        return await self._request("PUT", f"/gardens/{garden_id}/device/light-level", json_body=body)

    # Backwards-compatible helpers used earlier in the integration
    async def get_devices(self) -> Any:
        return await self.get_gardens()

    async def get_device_data(self, garden_id: int) -> Any:
        # map to device status
        return await self.get_device_status(garden_id)
