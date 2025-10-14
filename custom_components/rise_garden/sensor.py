from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
try:
    # Newer Home Assistant exposes UnitOfTemperature in homeassistant.const
    from homeassistant.const import UnitOfTemperature
except Exception:
    UnitOfTemperature = None

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    def _build_entities() -> list[SensorEntity]:
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

            _LOGGER.debug("Processing device id=%s name=%s", garden_id, name)

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

            # temperature sensor (if present) — support both data.at and top-level at
            temp_val = None
            if isinstance(status, dict):
                temp_val = status.get("data", {}).get("at") if isinstance(status.get("data"), dict) else None
                temp_top = status.get("at")
                if temp_val is None and temp_top is not None:
                    temp_val = temp_top
            if temp_val is not None:
                # choose metric path depending on where it was found
                metric_path = "data.at" if isinstance(status.get("data"), dict) and status.get("data", {}).get("at") is not None else "at"
                _LOGGER.debug("Adding temperature sensor for device %s (path=%s)", garden_id, metric_path)
                entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "temperature", metric_path))
            else:
                _LOGGER.debug("No temperature data for device %s (keys: %s)", garden_id, list(status.get("data", {}).keys()) if isinstance(status.get("data"), dict) else list(status.keys()) if isinstance(status, dict) else [])

            # light level sensor — check data.lamp_level and top-level lamp_level
            lamp_val = None
            if isinstance(status, dict):
                lamp_val = status.get("data", {}).get("lamp_level") if isinstance(status.get("data"), dict) else None
                lamp_top = status.get("lamp_level") or status.get("lampState") or status.get("lamp_state")
                if lamp_val is None and lamp_top is not None:
                    lamp_val = lamp_top
            if lamp_val is not None:
                # Do not create a separate sensor for lamp_level — the light
                # entity exposes the on/off and brightness (dimming) for the
                # garden. Creating a sensor for the lamp_level causes duplicate
                # unique_id conflicts and confuses the registry.
                _LOGGER.debug(
                    "Skipping creation of separate light-level sensor for device %s; light entity will represent lamp state/level",
                    garden_id,
                )
            else:
                _LOGGER.debug(
                    "No lamp_level data for device %s (keys: %s)",
                    garden_id,
                    list(status.get("data", {}).keys()) if isinstance(status.get("data"), dict) else list(status.keys()) if isinstance(status, dict) else [],
                )

            # moisture sensor removed — the garden API does not provide a
            # dedicated moisture sensor for all kits; we no longer create a
            # separate moisture entity to avoid confusion.

            # current water volume (gallons) — may be top-level or under data
            water_val = None
            if isinstance(status, dict):
                # check data node first, then top-level
                if isinstance(status.get("data"), dict) and status.get("data", {}).get("current_water_volume_gallons") is not None:
                    water_val = "data.current_water_volume_gallons"
                elif status.get("current_water_volume_gallons") is not None:
                    water_val = "current_water_volume_gallons"
            if water_val:
                _LOGGER.debug("Adding water-volume sensor for device %s (path=%s)", garden_id, water_val)
                entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "water_volume", water_val))
            else:
                _LOGGER.debug("No current_water_volume_gallons key for device %s", garden_id)

            # firmware version and wifi info (wifi_signal_strength, wifi_rssi)
            # firmware may be numeric or string; wifi_signal_strength is a human
            # readable string (e.g. "Very Good"); wifi_rssi is a numeric dBm value.
            if isinstance(status, dict):
                # firmware
                if (isinstance(status.get("data"), dict) and status.get("data", {}).get("firmware") is not None) or (status.get("firmware") is not None):
                    metric_path = "data.firmware" if isinstance(status.get("data"), dict) and status.get("data", {}).get("firmware") is not None else "firmware"
                    _LOGGER.debug("Adding firmware sensor for device %s (path=%s)", garden_id, metric_path)
                    entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "firmware", metric_path))

                # wifi_signal_strength (string)
                if (isinstance(status.get("data"), dict) and status.get("data", {}).get("wifi_signal_strength") is not None) or (status.get("wifi_signal_strength") is not None):
                    metric_path = "data.wifi_signal_strength" if isinstance(status.get("data"), dict) and status.get("data", {}).get("wifi_signal_strength") is not None else "wifi_signal_strength"
                    _LOGGER.debug("Adding wifi_signal_strength sensor for device %s (path=%s)", garden_id, metric_path)
                    entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "wifi_signal_strength", metric_path))

                # wifi_rssi (numeric dBm)
                if (isinstance(status.get("data"), dict) and status.get("data", {}).get("wifi_rssi") is not None) or (status.get("wifi_rssi") is not None):
                    metric_path = "data.wifi_rssi" if isinstance(status.get("data"), dict) and status.get("data", {}).get("wifi_rssi") is not None else "wifi_rssi"
                    _LOGGER.debug("Adding wifi_rssi sensor for device %s (path=%s)", garden_id, metric_path)
                    entities.append(RiseGardenMetricSensor(coordinator, garden_id, name, device_info, "wifi_rssi", metric_path))

        return entities

    async def _async_add_when_ready() -> None:
        """Build entities from coordinator data and add them to Home Assistant."""
        entities = _build_entities()
        if entities:
            async_add_entities(entities, True)

    # If coordinator already has data, add entities now. Otherwise register a
    # one-shot listener to add them once the first refresh finishes.
    if coordinator.data:
        await _async_add_when_ready()
    else:
        called = False

        def _on_coordinator_update() -> None:
            nonlocal called
            # guard so this runs only once (some HA versions don't implement
            # async_remove_listener)
            if called:
                return
            called = True
            hass.async_create_task(_async_add_when_ready())

        coordinator.async_add_listener(_on_coordinator_update)


class RiseGardenMetricSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor for a single metric on a Rise Garden device."""

    def __init__(self, coordinator: DataUpdateCoordinator, garden_id: Any, garden_name: str, device_info: DeviceInfo, metric: str, metric_path: str):
        super().__init__(coordinator)
        self._garden_id = garden_id
        self._metric = metric
        self._metric_path = metric_path.split(".")
        # Make metric names human-friendly (e.g. 'water_volume' -> 'Water Volume')
        self._attr_name = f"{garden_name} {metric.replace('_', ' ').title()}"
        self._device_info = device_info

        # sensible defaults; Home Assistant will accept None if unknown
        if metric == "temperature":
            # Do not hard-code the unit here; report the unit dynamically
            # via native_unit_of_measurement so the sensor respects the
            # Home Assistant unit system (C/F). We'll convert the value in
            # native_value when needed.
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "light":
            self._attr_native_unit_of_measurement = "%"
        elif metric == "water_volume":
            self._attr_native_unit_of_measurement = "gal"
            # Make water volume graphable as a measurement
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif metric == "wifi_rssi":
            # RSSI in dBm
            self._attr_native_unit_of_measurement = "dBm"
            self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        elif metric == "firmware":
            # firmware version, leave as plain value (no unit)
            pass
        elif metric == "wifi_signal_strength":
            # human-readable string, leave as plain value
            pass

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement for this sensor.

        For temperature sensors, return Home Assistant's configured unit so
        the UI shows values in the user's preferred units (°C or °F).
        """
        if self._metric == "temperature":
            # hass is available after entity is added
            if self.hass is None:
                return "°C"
            return self.hass.config.units.temperature_unit
        return getattr(self, "_attr_native_unit_of_measurement", None)

    @property
    def unique_id(self) -> str:
        # Namespace metric sensors to avoid colliding with other platform IDs
        return f"{self._garden_id}_metric_{self._metric}"

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
        # If this is a temperature metric, convert to the configured unit if necessary.
        if self._metric == "temperature":
            try:
                # assume API provides Celsius values
                c = float(node)
                # if HA is configured for Fahrenheit, convert
                # Prefer the UnitOfTemperature enum when available, fall back to
                # the raw unit string (°F) for older HA versions.
                temp_unit = getattr(self.hass.config.units, "temperature_unit", None) if self.hass else None
                if UnitOfTemperature is not None:
                    target_f = temp_unit == UnitOfTemperature.FAHRENHEIT
                else:
                    target_f = temp_unit == "°F"
                if target_f:
                    return round((c * 9.0 / 5.0) + 32.0, 1)
                return round(c, 1)
            except (ValueError, TypeError):
                return node

        return node
