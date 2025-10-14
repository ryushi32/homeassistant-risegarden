from __future__ import annotations

from typing import Any
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: DataUpdateCoordinator = data["coordinator"]
    client = data["client"]

    gardens = coordinator.data.get("devices", []) if coordinator.data else []
    entities: list[SwitchEntity] = []

    for garden in gardens:
        garden_id = garden.get("id") or garden.get("garden_id") or garden.get("gardenId")
        if garden_id is None:
            continue
        name = garden.get("name") or f"Rise Garden {garden_id}"
        entities.append(RiseGardenLightSwitch(coordinator, client, garden_id, name))

    async_add_entities(entities)


class RiseGardenLightSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator: DataUpdateCoordinator, client: Any, garden_id: Any, name: str):
        super().__init__(coordinator)
        self._client = client
        self._garden_id = garden_id
        self._attr_name = f"{name} Light"
        self._is_on = False

    @property
    def unique_id(self) -> str:
        return f"{self._garden_id}_light"

    @property
    def is_on(self) -> bool:
        # read current lamp_level from coordinator
        device_data = self.coordinator.data.get("device_data", {}) if self.coordinator.data else {}
        status = device_data.get(self._garden_id) or device_data.get(str(self._garden_id)) or {}
        lamp = status.get("data", {}).get("lamp_level")
        try:
            return bool(lamp and int(lamp) > 0)
        except Exception:
            return False

    async def async_turn_on(self, **kwargs):
        # set lamp level to 100
        try:
            await self._client.set_light_level(int(self._garden_id), 100)
            # refresh coordinator
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn on light for %s: %s", self._garden_id, err)

    async def async_turn_off(self, **kwargs):
        try:
            await self._client.set_light_level(int(self._garden_id), 0)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to turn off light for %s: %s", self._garden_id, err)
