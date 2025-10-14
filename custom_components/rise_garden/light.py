from __future__ import annotations

from typing import Any
import logging

from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _brightness_to_level(brightness: int) -> int:
    """Map Home Assistant brightness (0-255) to lamp level (0-100)."""
    if brightness <= 0:
        return 0
    return round((brightness / 255) * 100)


def _level_to_brightness(level: int) -> int:
    """Map lamp level (0-100) to Home Assistant brightness 0-255."""
    if level <= 0:
        return 0
    return round((level / 100) * 255)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    client = data["client"]

    gardens = coordinator.data.get("devices", []) if coordinator.data else []
    entities: list[LightEntity] = []

    for garden in gardens:
        garden_id = garden.get("id") or garden.get("garden_id") or garden.get("gardenId")
        if garden_id is None:
            continue
        name = garden.get("name") or f"Rise Garden {garden_id}"
        entities.append(RiseGardenLight(coordinator, client, garden_id, name))

    async_add_entities(entities)


class RiseGardenLight(CoordinatorEntity, LightEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, client: Any, garden_id: Any, name: str):
        super().__init__(coordinator)
        self._client = client
        self._garden_id = garden_id
        self._attr_name = f"{name} Light"

    @property
    def unique_id(self) -> str:
        return f"{self._garden_id}_light"

    @property
    def is_on(self) -> bool:
        device_data = self.coordinator.data.get("device_data", {}) if self.coordinator.data else {}
        status = device_data.get(self._garden_id) or device_data.get(str(self._garden_id)) or {}
        lamp = status.get("data", {}).get("lamp_level")
        try:
            return bool(lamp and int(lamp) > 0)
        except Exception:
            return False

    @property
    def brightness(self) -> int | None:
        device_data = self.coordinator.data.get("device_data", {}) if self.coordinator.data else {}
        status = device_data.get(self._garden_id) or device_data.get(str(self._garden_id)) or {}
        lamp = status.get("data", {}).get("lamp_level")
        try:
            if lamp is None:
                return None
            return _level_to_brightness(int(lamp))
        except Exception:
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        # brightness is 0-255; default to 255
        brightness = kwargs.get("brightness", 255)
        level = _brightness_to_level(int(brightness))
        try:
            await self._client.set_light_level(int(self._garden_id), level)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set light level for %s: %s", self._garden_id, err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self._client.set_light_level(int(self._garden_id), 0)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off light for %s: %s", self._garden_id, err)
