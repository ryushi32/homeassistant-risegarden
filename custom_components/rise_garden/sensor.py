from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = coordinator.data.get("devices", []) if coordinator.data else []

    entities: list[SensorEntity] = []

    for device in devices:
        # robustly get garden id from possible keys
        garden_id = device.get("id") or device.get("garden_id") or device.get("gardenId")
        if garden_id is None:
            _LOGGER.debug("Skipping device without id: %s", device)
            continue

        name = device.get("name") or device.get("garden_name") or f"Rise Garden {garden_id}"

        # prepare device_info for entity registry
        device_info = DeviceInfo(
            identifiers={(DOMAIN, str(garden_id))},
            name=name,
            manufacturer=device.get("manufacturer") or device.get("vendor") or "Rise Gardens",
            model=device.get("model"),
            via_device=None,
        )

        # determine available metrics from the already-fetched device_data
        status = None
        device_data = coordinator.data.get("device_data", {}) if coordinator.data else {}
        # support both int and str keys
        if garden_id in device_data:
            status = device_data[garden_id]
        elif str(garden_id) in device_data:
            status = device_data[str(garden_id)]
        else:
            status = {}

        # temperature sensor (if present)
        if status.get("data", {}).get("at") is not None:
            entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "temperature", "data.at"))

        # light level sensor
        if status.get("data", {}).get("lamp_level") is not None:
            entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "light", "data.lamp_level"))

        # moisture - may be at several keys; try a few common names
        moisture_val = None
        for key in ("moisture", "soil_moisture", "moisture_level", "water_level"):
            if status.get("data", {}).get(key) is not None:
                moisture_val = key
                break
        if moisture_val:
            entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "moisture", f"data.{moisture_val}"))

    async_add_entities(entities, True)


class RiseGardenMetricSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor for a single metric on a Rise Garden device."""

    def __init__(self, coordinator: DataUpdateCoordinator, garden_id: Any, garden_name: str, device_info: DeviceInfo, metric: str, metric_path: str):
        super().__init__(coordinator)
        self._garden_id = garden_id
        self._metric = metric
        self._metric_path = metric_path.split(".")
        self._attr_name = f"{garden_name} {metric.capitalize()}"
        self._device_info = device_info

        # sensible defaults; Home Assistant will accept None if unknown
        if metric == "temperature":
            self._attr_native_unit_of_measurement = "°C"
            self._attr_device_class = "temperature"
            self._attr_state_class = "measurement"
        elif metric == "light":
            self._attr_native_unit_of_measurement = "%"
        elif metric == "moisture":
            self._attr_native_unit_of_measurement = "%"

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def unique_id(self) -> str:
        return f"{self._garden_id}_{self._metric}"

    @property
    def native_value(self) -> Any:
        """Return the metric value from the coordinator data."""
        device_data = self.coordinator.data.get("device_data", {}) if self.coordinator.data else {}

        status = None
        if self._garden_id in device_data:
            status = device_data[self._garden_id]
        elif str(self._garden_id) in device_data:
            status = device_data[str(self._garden_id)]
        else:
            status = {}

        # traverse metric_path
        node = status
        for key in self._metric_path:
            if not isinstance(node, dict):
                return None
            node = node.get(key)
            if node is None:
                return None
        return node
